import os
from yaml import Dumper, dump as dump_yaml

def create_workdir(result_dir, sample, singularity_img,
                   singularity_bind, params):
    
    params['results directory'] = result_dir
    
    ## prepare parameter file
    if singularity_img is not None:
        params['with-singularity'] = singularity_img
        params['singularity-bind'] = singularity_bind

    param_file = os.path.join(result_dir, f'{sample}_params.yaml')

    if os.path.exists(param_file):
        # already done
        return
    os.system(f"mkdir -p {result_dir}")

    # actual files
    if os.path.exists('bin'):
        os.system(f"cp -r bin {result_dir}/")

    out = open(param_file, 'w', encoding='utf-8')
    ## TODO: check if differences in parameters (e.g. singularity or versions)
    out.write(dump_yaml(params, Dumper=Dumper))
    out.close()
