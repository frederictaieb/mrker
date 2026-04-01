
import os
import shutil
def delete_path(path: str):
    import os, shutil

    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)