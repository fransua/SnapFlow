import os
from yaml import Dumper, dump as dump_yaml
import inspect


def get_caller_script_path():
    # Get the frame of the caller
    caller_path = os.path.split(inspect.stack()[2].filename)[0]
    # Get the absolute path of the caller script
    return os.path.abspath(caller_path)


def create_workdir(result_dir, sample, singularity_img,
                   singularity_binds, params):
    """
    :param result_dir: path for the global output directory
    :param sample: sample name to search for in the params dictionary (from the input YAML file)
    :param singularity_img: path to a singularity image -> this will automatically
       update the params dictionary
    :param singularity_bind: path to a singularity bind directory (to be included
    in the singularity scope) -> this will automatically update the params dictionary
    :param params: dictionary of parameters set and parsed from the input YAML file.
    """
    params['results directory'] = result_dir
    
    ## prepare parameter file
    if singularity_img is not None:
        params['with-singularity'] = singularity_img
        params['singularity-bind'] = singularity_binds

    param_file = os.path.join(result_dir, f'{sample}_params.yaml')

    # if os.path.exists(param_file):
    #     # already done
    #     return
    os.system(f"mkdir -p {result_dir}")

    # copy executable files and scripts
    bin_path = os.path.join(get_caller_script_path(), 'bin')
    if os.path.exists(bin_path):
        os.system(f"cp -r {bin_path} {result_dir}/")

    out = open(param_file, 'w', encoding='utf-8')
    ## TODO: check if differences in parameters (e.g. singularity or versions)
    out.write(dump_yaml(params, Dumper=Dumper))
    out.close()

