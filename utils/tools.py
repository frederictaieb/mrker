#utils/tools.py

def format_duration_ms(duration_ms: int | None) -> str:
    if not duration_ms:
        return "0:00"

    total_seconds = duration_ms // 1000
    minutes = total_seconds // 60
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:02d}"