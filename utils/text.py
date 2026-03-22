#utils/text.py

import re
import unicodedata

def ascii_clean(text: str) -> str:
    if not text:
        return ""

    replacements = {
        "æ": "ae",
        "Æ": "AE",
        "œ": "oe",
        "Œ": "OE",
        "ð": "d",
        "Ð": "D",
        "þ": "th",
        "Þ": "Th",
        "ł": "l",
        "Ł": "L",
    }

    for src, dst in replacements.items():
        text = text.replace(src, dst)

    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    return text


def sanitize_filename_part(text: str) -> str:
    text = ascii_clean(text)
    text = re.sub(r'[<>:"/\\|?*]', " ", text)
    text = re.sub(r"[\r\n\t]", " ", text)
    text = re.sub(r"[^\w\s\-\[\]&',.+]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text.rstrip(" .")


def smart_truncate(text: str, max_len: int) -> str:
    if len(text) <= max_len:
        return text

    truncated = text[:max_len].rstrip()
    last_space = truncated.rfind(" ")

    if last_space > max_len * 0.6:
        truncated = truncated[:last_space].rstrip()

    return truncated.rstrip(" ._-,")


def shorten_artists(artist_text: str, max_artists: int = 2) -> str:
    artists = [a.strip() for a in artist_text.split(",") if a.strip()]

    if len(artists) <= max_artists:
        return ", ".join(artists)

    return f"{artists[0]}, {artists[1]} +{len(artists) - max_artists}"


def clean_album(album: str) -> str:
    if not album:
        return ""

    a = album

    useless_patterns = [
        r"\(Original Motion Picture Score\)",
        r"\(Original Soundtrack\)",
        r"\(Bande originale.*?\)",
        r"\(Deluxe\)",
        r"\(Deluxe Edition\)",
        r"\(Expanded Edition\)",
        r"\(Remastered.*?\)",
    ]

    for pattern in useless_patterns:
        a = re.sub(pattern, "", a, flags=re.IGNORECASE)

    a = re.sub(r"\s+", " ", a).strip()
    a = a.rstrip(" -")
    return a


def clean_title(title: str, album: str) -> str:
    if not title:
        return ""

    t = title.strip()

    t = re.sub(r"\s*\(feat\..*?\)", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*\[feat\..*?\]", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+feat\..*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+ft\..*$", "", t, flags=re.IGNORECASE)

    t = re.sub(r'\s*-\s*from\s*".*?"', "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*-\s*from\s*'.*?'", "", t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(\s*from\s*".*?"\s*\)', "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*\(\s*from\s*'.*?'\s*\)", "", t, flags=re.IGNORECASE)

    useless_patterns = [
        r"\(Original Motion Picture Score\)",
        r"\(Original Soundtrack\)",
        r"\(Bande originale.*?\)",
        r"\(.*?Remastered.*?\)",
        r"\(.*?Version.*?\)",
    ]

    for pattern in useless_patterns:
        t = re.sub(pattern, "", t, flags=re.IGNORECASE)

    t = re.sub(r"\s+", " ", t).strip()
    t = t.rstrip(" -")

    album_simple = ascii_clean(clean_album(album)).lower().strip()
    title_simple = ascii_clean(t).lower().strip()

    if album_simple and title_simple != album_simple:
        if title_simple.endswith(" - " + album_simple):
            t = t[: -(len(album) + 3)].rstrip(" -")

    return t

def build_filename(artist: str, album: str, title: str, ext: str = ".mp3") -> str:
    artist = shorten_artists(artist, 2)
    album = clean_album(album)

    artist = sanitize_filename_part(artist)
    album = sanitize_filename_part(album)
    title = sanitize_filename_part(title)

    if not title:
        title = "untitled"

    artist = smart_truncate(artist, 40)
    album = smart_truncate(album, 50)
    title = smart_truncate(title, 60)

    filename = f"{artist} [{album}] {title}{ext}"

    max_len = 140

    if len(filename) > max_len and len(album) > 15:
        overflow = len(filename) - max_len
        album = smart_truncate(album, max(15, len(album) - overflow))
        filename = f"{artist} [{album}] {title}{ext}"

    if len(filename) > max_len and len(title) > 20:
        overflow = len(filename) - max_len
        title = smart_truncate(title, max(20, len(title) - overflow))
        filename = f"{artist} [{album}] {title}{ext}"

    if len(filename) > max_len and len(artist) > 15:
        overflow = len(filename) - max_len
        artist = smart_truncate(artist, max(15, len(artist) - overflow))
        filename = f"{artist} [{album}] {title}{ext}"

    return filename
