import os
from time import time

class FileLock:
    def __init__(self, target_file):
        self.target_file = target_file
        self.lock_file = f"{target_file}.lock"
    
    def __enter__(self):
        # acquire file lock
        while True:
            try:
                fd = os.open(self.lock_file, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
                os.close(fd)
                break  # ready to do somthing with the locked file
            except FileExistsError:
                time.sleep(0.1)
    
    def __exit__(self, exc_type, exc_value, traceback):
        # release the lock, be happy
        if os.path.exists(self.lock_file):
            os.remove(self.lock_file)
