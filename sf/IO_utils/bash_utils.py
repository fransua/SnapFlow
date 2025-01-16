

def color_status(status: str, l_align: int=0, r_align: int=0):
    """
    Set color based on status
    """
    lstatus = status.lower()  # reduces the amount of checks
    if lstatus in ['error', 'missing output']:
        status = f"{status} ✗"
        color = '\033[31m'  # Red
    elif lstatus == 'done':
        status = f"{status} ✔"
        color = '\033[32m'  # Green
    elif lstatus == 'running':
        color = '\033[93m'  # Orange (Yellow)
    elif lstatus in ['pending', '']:
        status = 'pending ⧖'
        color = '\033[37m'  # light Gray
    elif lstatus == 'dependent':
        status = 'dependent ⧗'
        color = '\033[37m'  # light Gray
    elif lstatus == 'unsatisfiable':
        status = "dependency ✗"
        color = '\033[93m'  # Red
    else:
        color = '\033[0m'   # Default color (reset)
    if l_align:
        if r_align:
            raise SyntaxError('should use either l_align or r_align, not both')
        status = f'{status:<{l_align}}'
    if r_align:
        status = f'{status:>{r_align}}'
    return f"{color}{status}\033[0m"


def tail(file_path, n=10):
    """
    Reads the last n lines of a file.

    Args:
        file_path (str): Path to the file.
        n (int): Number of lines to read from the end of the file.

    Returns:
        list: The last n lines of the file.
    """
    with open(file_path, 'rb') as f:
        f.seek(0, 2)  # Move to the end of the file
        file_size = f.tell()
        block_size = 1024
        buffer = bytearray()
        lines_found = 0

        while file_size > 0 and lines_found <= n:
            read_size = min(block_size, file_size)
            file_size -= read_size
            f.seek(file_size)
            buffer = f.read(read_size) + buffer  # Prepend new data

            # Count newlines in the buffer
            lines_found = buffer.count(b'\n')

        # Decode and split lines
        lines = buffer.decode(errors='ignore').splitlines()

    # Return the last n lines
    return lines[-n:]
