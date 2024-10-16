import os
from yaml import Dumper, dump as dump_yaml

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
    if os.path.exists('bin'):
        os.system(f"cp -r bin {result_dir}/")

    out = open(param_file, 'w', encoding='utf-8')
    ## TODO: check if differences in parameters (e.g. singularity or versions)
    out.write(dump_yaml(params, Dumper=Dumper))
    out.close()


class InvalidPathError(ValueError):
    """Exception raised for invalid file or directory path strings."""
    def __init__(self, path_str, invalid_chars, message="Invalid path string."):
        self.path_str = path_str
        self.message = (
            f"{message} The string '{path_str}' contains forbidden"
            f" characters or patterns (such as any of: {invalid_chars}).")
        super().__init__(self.message)

def validate_path(path_str, directory=False):
    # define invalid characters for paths
    if directory:
        invalid_chars = '<>"\\ | '
    else:
        invalid_chars = '<>"/\\|? *'
    if any(char in path_str for char in invalid_chars):
        raise InvalidPathError(path_str, invalid_chars)
    if path_str.startswith('-'):
        raise InvalidPathError(path_str, "starting with a dash")

    if path_str in ['.', '..']:
        raise InvalidPathError(path_str, "being single or double dot")

    return path_str

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
