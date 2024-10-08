#!/usr/bin/env python

import sys

from argparse import ArgumentParser
from yaml import Loader, load as load_yaml

from sf import Process_dict, create_workdir

sys.path.append('modules')

from modules.sequence_transformation import split_sequences, reverse
from modules.Sequence_stats import count_bases


def main():
    opts = get_options()

    yaml_params        = opts.yaml_params    # metadata

    sample             = opts.sample         # which to run
    result_dir         = opts.outdir         # where to run it
    singularity_img    = opts.singularity    # what to run with
    sif_bind           = opts.sif_bind       # mount path for singularity

    params = load_yaml(open(yaml_params, 'r' , encoding='utf-8'), Loader=Loader)

    try:
        params = params[sample]
    except KeyError:
        raise KeyError(f'ERROR: sample name should be one of: [{", ".join(list(params.keys()))}]')

    # prepare working directory
    create_workdir(result_dir, sample, singularity_img, sif_bind, params)

    ###########################################################################
    # START WORKFLOW

    # place to store workflow jobs:
    processes = Process_dict(params, name='Basic pipeline')

    ## Split sequences in the fasta into different files
    for rep, replicate in enumerate(params['input'], 1):
        splitted = split_sequences(replicate, replicate_name=f"rep{rep}", time="5:00")

        ## Reverse each sequence
        reverse(splitted, replicate_name=f"rep{rep}", time="1:00")
        
        count_bases(splitted, replicate_name=f"rep{rep}", time="2:00")

    ####
    # END WORKFLOW
    processes.write_commands(opts.sequential)
    processes.do_mermaid(result_dir, hide_files=False)

def get_options():
    parser = ArgumentParser()

    parser.add_argument('--sample', metavar='STR', required=True,
                        default=False,
                        help='''name of the sample to process
                        (should match name in the YAML parameter file)''')
    parser.add_argument('-o', dest='outdir', metavar='PATH', required=True,
                        help='''path to output directory''')
    parser.add_argument('-p', '--yaml_params', metavar='PATH', required=True,
                        help='''path to YAML file with the list of experiments and
                        associated metadata and parameters for the pipeline.''')
    parser.add_argument('--singularity', metavar='PATH', default=None,
                        help='PATH to singularity file to be used.')
    parser.add_argument('--sif_bind', metavar='PATH', default=None,
                        help='PATH to folder to bind to singularity')
    parser.add_argument('--sequential', action='store_true',
                        help='''outputs commands without depencies or cpu/time indications.''')
    opts = parser.parse_args()
    return opts


if __name__ == "__main__":
    exit(main())
