

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
