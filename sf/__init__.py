import os
import sys
import functools
from sf.utils import create_workdir
from sf import globals


def rule(func):
    """
    SnapFlow decorator to create Process from a rule function.
    rule functions need to declare at least 4 variables:
     - "name"  : the name of the process (should be unique)
     - "input_": a Dictionary listing needed input files
     - "output": a Dictionary listing generated output files 
     - "cmd"   : the command to be executed
     
    On top of this, the rule function should take at least two positional arguments:
     - a Process_dict instance
     - a dictionary with parameters
     
    and it should also have the `**kwargs` argument.
    
     -> The rule decorator will populate the kwargs argument with the "workdir" key to be used
    for the definition of output paths.
    """
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        # Working directory is created in a hierarchy corresponding
        # to the module hierarchy of the function called... just brilliant
        # processes = args[0]
        name           = func.__name__
        modules        = func.__module__.split('.')[1:] + [name]
        replicate_name = kwargs.get('replicate_name')

        if replicate_name:
            replicate_name = kwargs.get('replicate_name')
            workdir = os.path.join(
                    globals.processes.result_dir, 'tmp',
                    *[*modules, replicate_name])
            name = f"{name}_{replicate_name}"
        else:
            workdir = os.path.join(
                    globals.processes.result_dir, 'tmp', modules)
        kwargs['workdir'] = workdir
        
        rule_vars = {}
        def tracer(frame, event, arg):
            if event == 'return':
                rule_vars.update(frame.f_locals)
            return tracer
        sys.setprofile(tracer)
        
        func(*args, **kwargs)
        
        sys.setprofile(None)
        
        # check all variables are created:
        diff = set(['input_', 'output', 'cmd']).difference(rule_vars)
        if diff:
            raise TypeError('ERROR: missing variables to be defined in '
                            f'{func.__module__}.{name}:\n {", ".join(diff)}')
        
        proc = Process(input_=rule_vars['input_'], workdir=workdir, output=rule_vars['output'],
                       command=rule_vars['cmd'], name=name, module=modules)
        globals.processes[name] = proc
        return proc
    return wrapper

class IO_type:
    def __init__(self, type_, value, process=None) -> None:
        self.type = type_
        self.process = process
        self.name = os.path.split(value)[-1] if process is None else value
        if self.process is None:
            self.value = value
        else:
            self.value = process.output[value]
        if not self.validate():
            raise TypeError(f"{self} not a {type_}")

    def __repr__(self) -> str:
        return self.value

    def validate(self):
        if self.process is None and self.type == "path":
            return os.path.exists(self.value)
        if self.type == "int":
            try:
                self.value = int(self.value)
                return True
            except (ValueError, TypeError):
                return False
        if self.type == "float":
            try:
                self.value = float(self.value)
                return True
            except (ValueError, TypeError):
                return False
        return True


class Process_dict(dict):
    def __init__(self, params, name=None, *args, **kwargs):
        self.update(*args, **kwargs)
        if params.get('with-singularity', None) is not None:
            if  params.get('singularity-bind', None) is not None:
                bind = f"--bind {params['singularity-bind']} "
            else:
                bind = ''
            self.singularity  = f"singularity exec {bind}{params['with-singularity']} "
        else:
            self.singularity  = ''

        self.result_dir = params['results directory']
        
        self.name = name

        # to hold conversion table -> useful for meta-processes (1 job, several commands)
        self.synonyms = {}
        globals.processes = self

    def __setitem__(self, key, process):
        if key in self:
            raise KeyError(f"Key {key} already defined. Add the "
                           "`replicate_name` argument to your Rule call.")
        if process.singularity == '':
            process.singularity = self.singularity
        dict.__setitem__(self, key, process)

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            return dict.__getitem__(self, self.synonyms[key])
    
    def write_commands(self, opts) -> None:
        pid = 1
        for name, process in self.items():
            # TODO: write memory 
            # # (memory per cpu should be written in order to compute number of cpus needed)
            if process.is_done():
                continue
            dependencies = []
            for dep in process.dependencies:
                try:
                    dependencies.append(str(self[dep].pid))
                except AttributeError:  # dependency already satisfied
                    continue
            process.pid = pid
            if not process.is_done():
                process.format_executable()
            if dependencies:
                dependencies = f";depe {','.join(dependencies)}"
            else:
                dependencies = ''
            if opts.sequential:
                prefix = ''
            else:
                prefix = ("["
                        f"name scHiC-{name.replace(' ', '_')};"
                        f"cpus-per-task {process.cpus};"
                        f"time {process.time}"
                        f"{dependencies}"
                        f"] {process.singularity} ")
            print(prefix + f"/bin/bash {os.path.join(process.workdir, '.command.sh')}")
            pid += 1


    def do_mermaid(self, result_dir: str) -> None:
        from python_mermaid.diagram import MermaidDiagram, Node, Link
        
        groups = set(p.module for p in self.values())
        nodes = [Node(n.lower()) for n in groups]
        nid = {}
        nio = {}
        pid = 0
        links = []
        for g in nodes:
            for n, p in self.items():
                if p.module.lower()==g.id:
                    this_node = Node(p.rule_name, shape="circle")
                    g.add_sub_nodes([this_node])
                    p.pid = pid
                    nid[pid] = this_node
                    for o in p.output:
                        nio[o.lower()] = Node(o.lower(), shape="hexagon")
                        g.add_sub_nodes([nio[o.lower()]])
                        links.append(Link(this_node, nio[o.lower()]))
                    for i in p.input.values():
                        if i.name.lower() not in nio:  # it's an output from somewhere else
                            nio[i.name.lower()] = Node(i.name.lower(), shape='cylindrical')
                        links.append(Link(nio[i.name.lower()], this_node))
                    pid += 1
        chart = MermaidDiagram(
        title=self.name,
        nodes=nodes + list(nio.values()),
        links=links)

        out = open(os.path.join(result_dir, 'DAG.mmd'), 'w', encoding='utf-8')
        out.write(str(chart))
        out.close()



class Process:
    """
    job/process metadata class
    """
    def __init__(self, input_: dict, output: dict, workdir: str, module:str,
                 command: str, name: str, outvar: dict={}, publish=None,
                 cpus=1, memory=1, time=1, singularity=None, env=None) -> None:
        """
        params None publish: should be a list of pair of path. Within each pair,
           the first element should be the result file to "publish", and the
           second element the destination forder.
        """
        self.module, self.rule_name = module[-2:]
        self.workdir      = workdir
        os.system(f'mkdir -p {workdir}')
        self.input        = input_
        self.output       = output
        self.outvar       = outvar
        if outvar:
            self.output.update(outvar)
        self.command      = command
        self.name         = name
        self.dependencies = set(v.process.name for v in self.input.values()
                                if v.process is not None)
        self.cpus         = cpus
        self.memory       = memory   # Gb
        self.time         = time     # hours

        self.status       = False

        self.publish      = []
        
        self.update_publish_info(publish)
                
        self.env         = '' if env         is None else env          # TODO: implement
        self.singularity = '' if singularity is None else singularity

        # gets an error if something missing:
        self.check_input()
        # checks that all outputs are there
        # and that process finished succesfully
        # if not self.is_done():
        #     self.format_executable()

    def update_publish_info(self, publish):
        if publish is not None:
            if not isinstance(publish, list) and not isinstance(publish, tuple):
                raise TypeError("ERROR: 'publish' should be a list or tuple.")
            for origin_file, *destiny in publish:
                dest_name = os.path.join(*destiny)  # dirty trick for renaming possibility
                os.system(f'mkdir -p {destiny[0]}')
                self.publish.append(f"cp -rf {origin_file} {dest_name}")

    def format_executable(self):
        script = PROCESS_SCRIPT.format(
            WORKDIR=self.workdir,
            ENV=self.env,
            CMD=self.command,
            PUBLISH=' && '.join(self.publish) if self.publish else f'echo {self.name}')
        out = open(os.path.join(self.workdir, '.command.sh'), 'w', encoding='utf-8')
        out.write(script)
        out.close()

    def is_done(self):
        """
        Checks if a given process has laready been run
        """
        if (os.path.exists(os.path.join(self.workdir, '.done')) and
            self.check_output()):
            self.status = "done"
            return True
        self.status = "pending"
        return False

    def check_input(self):
        """
        Check if all input files are accessible
        """
        errors = []
        for fpath in self.input.values():
            if fpath.type != 'path':
                continue
            if fpath.process is None and not os.path.exists(str(fpath)):
                errors.append(str(fpath))
        if errors:
            errors = '\n - '.join(errors) + '\n'
            raise FileNotFoundError(f"Missing inputs: {errors}")

    def check_output(self):
        """
        Check if all output files are generated
        """
        for output, fpath in self.output.items():
            if not os.path.exists(fpath) and output not in self.outvar:
                return False
        return True

PROCESS_SCRIPT = '''
#! /bin/bash

{ENV}

{CMD} 2> {WORKDIR}/.command.err 1> {WORKDIR}/.command.out && echo ok > {WORKDIR}/.done

{PUBLISH} ||  rm -f {WORKDIR}/.done

'''
