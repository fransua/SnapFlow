#!/usr/bin/env python

import os
import sys

from argparse import ArgumentParser
from yaml import Loader, load as load_yaml

from sf import Process_dict, create_workdir

sys.path.append('modules')

from modules.align.prepare_refseq     import get_refseq, index_refseq


def main():
    opts = get_options()

    yaml_params        = opts.yaml_params    # metadata

    sample             = opts.sample         # which to run
    config             = opts.config         # how to run it
    result_dir         = opts.outdir         # where to run it
    singularity_img    = opts.singularity    # what to run with

    params = load_yaml(open(yaml_params, 'r' , encoding='utf-8'), Loader=Loader)

    try:
        params = params[sample]
    except KeyError:
        raise KeyError(f'ERROR: sample name should be one of: [{", ".join(list(params.keys()))}]')

    # prepare working directory
    create_workdir(result_dir, sample, config, singularity_img,
                   params)

    ###########################################################################
    # START WORKFLOW

    ref_base_name = os.path.split(params['ref_genome'])[-1]
    ref_base_name = ref_base_name.replace('.gz'   , '')
    ref_base_name = ref_base_name.replace('.zip'  , '')
    ref_base_name = ref_base_name.replace('.fasta', '')
    ref_base_name = ref_base_name.replace('.fa'   , '')
    params['ref_base_name'] = ref_base_name

    # place to store workflow jobs:
    processes = Process_dict(params)

    ## Get refseq
    get_refseq(processes, result_dir, params)

    ## Index reference genome
    index_refseq(processes, result_dir, params, cpus=12)

    for read in ['1', '2']:
        for replicate in params['hic_replicate']:
            ## Trimming (uncompressing only)  # TODO: extend to true trimmer
            hic_trimming(processes, result_dir, params, replicate, read)

            ## Hi-C QC
            hic_qc(processes, result_dir, params, replicate, read)

            ## Mapping full
            map_hic_full(processes, result_dir, replicate, read, cpus=12)

            ## Separate mapped/unmapped
            rescue_unmapped(processes, result_dir, replicate, read)

            ## Split by restriction site
            split_re_sites(processes, result_dir, replicate, read, params)

            ## Mapping fragments
            map_hic_frag(processes, result_dir, replicate, read, cpus=12)

        ## Merge by read-end
        merge_by_read_end(processes, result_dir, params, read, cpus=12)

    ## Parse mapped reads from both ends
    parse_mapped(processes, result_dir, params)

    ## Intersect both read ends
    intersect_read_ends(processes, result_dir)

    ## Filter ditags
    filter_ditags(processes, result_dir, params, cpus=4)

    ## Demultiplex
    demultiplex(processes, result_dir, params)

    ## Multiplet detection
    find_multiplets(processes, result_dir, params, cpus=8)
    
    ## Single-cell selection and compute stats
    select_cells(processes, result_dir, params)

    ## Format single-cells to be used as pseudo-bulk
    format_single_cells(processes, result_dir)
    
    if 'adt_replicate' in params:
        for replicate in params['hic_replicate']:
            ## Check contamination of ADTs in genomic sample
            check_ADT_contamination(processes, result_dir, params, replicate)
        for replicate in params['adt_replicate']:
            for read in ['1', '2']:
                ## Trimming (uncompressing only)  # TODO: extend to true trimmer
                adt_trimming(processes, result_dir, params, replicate, read)
            ## map ADTs
            map_ADTs(processes, result_dir, params, replicate)

    ## Normalize Hi-C and call TADs/compartments
    normalize_hic(processes, result_dir, params, cpus=8)
    
    ## Bulk summary plot
    bulk_summary_stats(processes, result_dir, params, sample)

    ####
    # END WORKFLOW
    processes.write_commands(opts)
    processes.do_mermaid(result_dir)

def get_options():
    parser = ArgumentParser()

    parser.add_argument('--sample', metavar='STR', required=True,
                        default=False,
                        help='''name of the sample to process
                        (should match name in the YAML parameter file)''')
    parser.add_argument('-c', '--config', metavar='PATH', required=True,
                        help='config file to use.')
    parser.add_argument('-o', dest='outdir', metavar='PATH', required=True,
                        help='''path to output directory''')
    parser.add_argument('-p', '--yaml_params', metavar='PATH', required=True,
                        help='''path to YAML file with the list of experiments and
                        associated metadata and parameters for the pipeline.''')
    parser.add_argument('--singularity', metavar='PATH', default=None,
                        help='PATH to singularity file to be used.')
    parser.add_argument('--sequential', action='store_true',
                        help='''outputs commands without depencies or cpu/time indications.''')
    opts = parser.parse_args()
    return opts


if __name__ == "__main__":
    exit(main())
