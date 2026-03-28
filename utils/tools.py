#utils/tools.py

import os
def delete_path(path: str):
    import os, shutil

    if os.path.isfile(path) or os.path.islink(path):
        os.remove(path)
    elif os.path.isdir(path):
        shutil.rmtree(path)

def format_duration_ms(duration_ms: int | None) -> str:
    if not duration_ms:
        return "0:00"

    total_seconds = duration_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"

def ms_to_hms(ms: int) -> str:
    seconds = ms // 1000
    h = seconds // 3600
    m = (seconds % 3600) // 60
    s = seconds % 60
    return f"{h:02}:{m:02}:{s:02}"

def ms_to_hms_d(ms: int) -> str:
    seconds = ms / 1000
    h = int(seconds // 3600)
    m = int((seconds % 3600) // 60)
    s = int(seconds % 60)
    d = int((seconds - int(seconds)) * 10)  # décisecondes

    return f"{h:02}:{m:02}:{s:02}.{d}"

def ms_to_hms_dcm(ms: int, precision: str = "ms") -> str:
    """
    precision:
        "d"  -> décisecondes   (1 chiffre)
        "c"  -> centisecondes  (2 chiffres)
        "ms" -> millisecondes  (3 chiffres)
    """

    seconds_total = ms // 1000
    remainder_ms = ms % 1000

    h = seconds_total // 3600
    m = (seconds_total % 3600) // 60
    s = seconds_total % 60

    if precision == "d":
        frac = remainder_ms // 100  # 1 chiffre
        return f"{h:02}:{m:02}:{s:02}.{frac}"

    elif precision == "c":
        frac = remainder_ms // 10   # 2 chiffres
        return f"{h:02}:{m:02}:{s:02}.{frac:02}"

    elif precision == "ms":
        return f"{h:02}:{m:02}:{s:02}.{remainder_ms:03}"

    else:
        raise ValueError("precision must be 'd', 'c', or 'ms'")