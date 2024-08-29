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


def transform_path_to_absolute(path):
    if isinstance(path, list) or isinstance(path, tuple):
        paths = []
        for p in path:
            if isinstance(p, str) and os.path.exists(p):
                paths.append(os.path.abspath(p))
            else:
                paths.append(p)
        return paths
    if isinstance(path, str) and os.path.exists(path):
        return os.path.abspath(path)
    return path

def make_path_absolute(params):
    for key, value in params.items():
        if isinstance(value, dict):
            # Recursively apply transformation to nested dictionaries
            make_path_absolute(value)
        else:
            # Apply the transformation function to the value in place
            params[key] = transform_path_to_absolute(value)
