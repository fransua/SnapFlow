import os
from glob import glob
from sf import IO_type, Process


def get_refseq(processes, result_dir, params):
    workdir  = os.path.join(result_dir, 'tmp', '01_refseq', 'parse_refseq')

    input_  = {
        'ref_base_name': IO_type('str' , params['ref_base_name']),
        'ref_seq_path' : IO_type('path', params['ref_genome']),
        }
    output = {
        'chromosome-sizes': os.path.join(workdir, 
                                   f"{input_['ref_base_name']}_chromosome-sizes.tsv"),
        }
    cmd = (f"python {result_dir}/bin/NF_free/get_chromosomes.py "
           f"{params['ref_genome']} {workdir} {output['chromosome-sizes']}")
    name='Get reference sequence'

    processes[name] = Process(input_=input_, workdir=workdir, output=output,
                              command=cmd, name=name)


def index_refseq(processes, result_dir, params, cpus):
    workdir  = os.path.join(result_dir, 'tmp', '01_refseq', 'index_refseq')
    os.system(f'mkdir -p {workdir}')
    input_  = {
        'ref_base_name': IO_type('str' , params['ref_base_name']),
        'ref_seq_path' : IO_type('path', params['ref_genome']),
        }

    output = {
        'index': f"{workdir}/{input_['ref_base_name']}.1.ht2",
        }

    outvar = {
        'index': f"{workdir}/{input_['ref_base_name']}",
        }

    if 'mapper_index' not in params or len(glob(params['mapper_index'])) == 0:
        # index does not exist, we create it:
        cmd = (f"bash {result_dir}/bin/NF_free/index_refgen.sh "
                f"{cpus} "
                f"{input_['ref_seq_path']} "
                f"{workdir}/{output['index']} "
                f"{workdir}")

    else:
        for index_path in glob(params['mapper_index']):
            os.system(f'ln -s {index_path} {workdir}/')
        cmd=''
        out = open(os.path.join(workdir, '.done'), 'w', encoding='utf-8')
        out.write('ok')
        out.close()

    name='Generate index of reference sequence'

    processes[name] = Process(input_=input_, workdir=workdir, output=output,
                              command=cmd, name=name, cpus=cpus, outvar=outvar)
