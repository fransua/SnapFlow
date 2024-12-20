import os


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
