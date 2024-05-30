import os
from yaml import Dumper, dump as dump_yaml

def create_workdir(result_dir, sample, config, singularity_img,
                   singularity_bind, params):
    ## prepare parameter file
    if singularity_img is not None:
        params['with-singularity'] = singularity_img
        params['singularity-bind'] = singularity_bind

    if os.path.exists(f"{result_dir}/bin"):
        # already done
        return
    os.system(f"mkdir -p {result_dir}")

    # actual files
    os.system(f"cp -r bin     {result_dir}/")
    os.system(f"cp {config}   {result_dir}/")

    param_file = os.path.join(result_dir, f'{sample}_params.yaml')
    out = open(param_file, 'w', encoding='utf-8')
    out.write(dump_yaml(params, Dumper=Dumper))  ## TODO: check if differences in parameters (e.g. singularity or versions)
    out.close()
