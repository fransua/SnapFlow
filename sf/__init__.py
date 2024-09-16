import os
import sys
import functools
from sf.utils import create_workdir, make_path_absolute
from sf.utils import validate_path
from sf import globals


def rule(func):
    """
    SnapFlow decorator to create Process from a rule function.
    rule functions need to declare at least 4 variables:
     - "input_": a Dictionary listing needed input files
     - "output": a Dictionary listing generated output files (should be relative path)
     - "cmd"   : the command to be executed
     
    Optionally we can also set:
     - "publish": a dictionary to copy most relevant output files to the `results` folder.
     
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

        if replicate_name is not None:
            validate_path(replicate_name)
            workdir = os.path.join(
                    globals.processes.result_dir, 'tmp',
                    *[*modules, replicate_name])
            name = f"{name}_{replicate_name}"
        else:
            workdir = os.path.join(
                    globals.processes.result_dir, 'tmp', *modules)
        
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
        
        proc = Process(input_=rule_vars['input_'], workdir=workdir,
                       output=rule_vars['output'], func_name=func.__name__,
                       command=rule_vars['cmd'], name=name, module=modules,
                       processes=globals.processes, publish=rule_vars.get('publish'),
                       **kwargs)
        globals.processes[name] = proc
        
        # define sisters: processes using the same function
        # (in order to ease the retrieval of outputs)
        if replicate_name is not None:
            if func.__name__ not in globals.processes.families:
                globals.processes.families[func.__name__] = {}
            globals.processes.families[func.__name__][name] = proc
            
        return proc
    return wrapper

class IO_type:
    def __init__(self, type_: str, value, process=None) -> None:
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
            self.value = os.path.abspath(self.value)
            return os.path.exists(self.value)
        elif self.type == "path":
            validate_path(self.value, directory=True)
            return True
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
    """
    Global dictionary to keep track of the processes to be executed.
    
    It takes as parameter a dictionary of parameters.
    """
    def __init__(self, params, name=None, *args, **kwargs):
        """
        :param params: dictionary of parameters
        """
        self.update(*args, **kwargs)
        if params.get('with-singularity', None) is not None:
            if  params.get('singularity-bind', None) is not None:
                bind = f"--bind {params['singularity-bind']} "
            else:
                bind = ''
            self.singularity  = f"singularity exec {bind}{params['with-singularity']} "
        else:
            self.singularity  = ''

        self.result_dir = os.path.abspath(params['results directory'])
        
        self.name = name

        # to hold conversion table -> useful for meta-processes (1 job, several commands)
        self.synonyms = {}
        self.families = {}
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
    
    def write_commands(self, sequential=True) -> None:
        """
        Write commands in stdout
        
        :param True sequential: if True commands are printed without any information
           about dependencies or number of cpus... They can be run directly in a
           sequential manner. Otherwise they will be printed preceded by a string 
           between brackets containing process specifications.
        """
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
            if sequential:
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
        """
        generates a mermaid Directed Acyclic Graph from the processes dictionary.
        """
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


class _Process_output(dict):
    """
    to store process output and relate the outputs of sister processes
    """
    def __init__(self, process, *args, **kwargs):
        self.update(*args, **kwargs)
        self.process = process

    def __getitem__(self, key):
        try:
            return dict.__getitem__(self, key)
        except KeyError:
            for sister in self.process.processes.families[self.process.func_name].values():
                if key in sister.output:
                    return sister.output[key]
        raise KeyError(f'key "{key}" not found')


class Process:
    """
    job/process metadata class
    """
    def __init__(self, input_: dict, output: _Process_output, workdir: str, 
                 module:str, command: str, name: str, processes: Process_dict,
                 func_name: str, publish=None, cpus=1, memory=1, time=1,
                 singularity=None, env=None, **kwargs) -> None:
        """
        inputs and outputs defined here are used to infer processes relational
        dependencies.
        
        :param input_: a dictionary of inputs. Values should be IO_type objects.
        :param output:  a dictionary of outputs.
        :param workdir: path where the process will be executed
        :param module: module where the Process function (with the @rule decorator)
           is defined
        :param command:        
        :param None publish: should be a list of pair of path. Within each pair,
           the first element should be the result file to "publish", and the
           second element the destination forder.
        """
        self.processes = processes
        self.module, self.rule_name = module[-2:]
        self.workdir      = workdir
        os.system(f'mkdir -p {workdir}')
        self.input        = input_
        self.func_name    = func_name
        # output paths that are not absolute are placed inside workdir
        for k, v in output.items():
            if not os.path.isabs(v):
                output[k] = os.path.join(self.workdir, v)
        self.output       = _Process_output(self, output)

        # commands including path to executable inside the bin folder are made absolute
        self.command      = command.replace(' bin/', f' {globals.processes.result_dir}/bin/')
        if self.command.startswith('bin/'):
            self.command = command.replace('bin/', f'{globals.processes.result_dir}/bin/')

        self.name         = name
        self.dependencies = set(v.process.name for v in self.input.values()
                                if v.process is not None)
        self.cpus         = cpus
        self.memory       = memory   # Gb
        self.time         = time     # hours

        self.status       = False

        self.publish      = []

        self.update_publish_info(publish)

        self.env         = '' if env         is None else env
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
                dest_name = os.path.join(globals.processes.result_dir, dest_name)
                os.system(f'mkdir -p {dest_name}')
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
            if not os.path.exists(fpath):
                return False
        return True

PROCESS_SCRIPT = '''
#! /bin/bash

set -euo pipefail  # any error or undefined variable or pipefail (respectively) will stop the script

{ENV}

cd {WORKDIR}

{CMD} 2> {WORKDIR}/.command.err 1> {WORKDIR}/.command.out && echo ok > {WORKDIR}/.done

{PUBLISH} ||  rm -f {WORKDIR}/.done

'''
