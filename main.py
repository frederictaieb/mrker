import os
import sys
import csv
import json
import re
import base64
import argparse
import unicodedata
from urllib.parse import urlparse
from dotenv import load_dotenv

import requests

load_dotenv()

SILENCE_TRACK = {
    "artist": "silence-10s",
    "title": "silence-10s",
    "album": "local",
    "spotify_link": "https://open.spotify.com/local///silence-10s/10",
    "filename": "silence-10s [local] silence-10s.mp3",
}


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

    # enlever feat.
    t = re.sub(r"\s*\(feat\..*?\)", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*\[feat\..*?\]", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+feat\..*$", "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s+ft\..*$", "", t, flags=re.IGNORECASE)

    # enlever "- from ..."
    t = re.sub(r'\s*-\s*from\s*".*?"', "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*-\s*from\s*'.*?'", "", t, flags=re.IGNORECASE)
    t = re.sub(r'\s*\(\s*from\s*".*?"\s*\)', "", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*\(\s*from\s*'.*?'\s*\)", "", t, flags=re.IGNORECASE)

    # suffixes fréquents
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

    # Ne jamais supprimer le titre s'il est exactement égal à l'album.
    # On ne retire une répétition que si le titre est plus long que l'album.
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


def extract_playlist_id(playlist_url: str) -> str:
    path = urlparse(playlist_url).path
    parts = [p for p in path.split("/") if p]
    if len(parts) >= 2 and parts[0] == "playlist":
        return parts[1]
    raise ValueError("URL de playlist Spotify invalide")


def get_access_token(client_id: str, client_secret: str) -> str:
    auth_string = f"{client_id}:{client_secret}"
    auth_b64 = base64.b64encode(auth_string.encode()).decode()

    response = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={
            "Authorization": f"Basic {auth_b64}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
        timeout=30,
    )
    response.raise_for_status()
    return response.json()["access_token"]


def get_playlist_tracks(playlist_id: str, access_token: str) -> list[dict]:
    tracks = []
    url = f"https://api.spotify.com/v1/playlists/{playlist_id}/tracks"
    headers = {"Authorization": f"Bearer {access_token}"}

    params = {
        "limit": 100,
        "fields": "items(track(name,external_urls,album(name),artists(name),is_local)),next"
    }

    while url:
        response = requests.get(url, headers=headers, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        for item in data.get("items", []):
            track = item.get("track")
            if not track:
                continue

            if track.get("is_local"):
                continue

            artists = ", ".join(artist["name"] for artist in track.get("artists", []))
            raw_title = track.get("name", "")
            raw_album = track.get("album", {}).get("name", "")
            spotify_link = track.get("external_urls", {}).get("spotify", "")

            album = clean_album(raw_album)
            title = clean_title(raw_title, raw_album)
            filename = build_filename(artists, album, title)

            tracks.append({
                "artist": artists,
                "title": title,
                "album": album,
                "spotify_link": spotify_link,
                "filename": filename,
            })

        url = data.get("next")
        params = None

    return tracks


def insert_silence_between_tracks(tracks: list[dict], silence_track: dict) -> list[dict]:
    if not tracks:
        return []

    result = []
    for i, track in enumerate(tracks):
        result.append(track)
        if i < len(tracks) - 1:
            result.append(silence_track.copy())
    return result


def save_to_csv(tracks: list[dict], filename: str = "playlist_tracks.csv") -> None:
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["artist", "title", "album", "spotify_link", "filename"]
        )
        writer.writeheader()
        writer.writerows(tracks)


def save_to_json(tracks: list[dict], filename: str = "playlist_tracks.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

def save_with_silence_to_csv(
    tracks: list[dict],
    filename: str = "spotify_links_with_silence.csv",
    silence_link: str = "https://open.spotify.com/local///silence-10s/10",
) -> None:
    """
    Crée un CSV avec une seule colonne: spotify_link
    et insère un lien de silence entre chaque track.
    """
    with open(filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["spotify_link"])

        for i, track in enumerate(tracks):
            writer.writerow([track.get("spotify_link", "")])

            if i < len(tracks) - 1:
                writer.writerow([silence_link])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Récupère les morceaux d'une playlist Spotify et génère un CSV et un JSON."
    )
    parser.add_argument(
        "playlist",
        help="URL de la playlist Spotify"
    )
    parser.add_argument(
        "-c",
        "--csv",
        default="playlist_tracks.csv",
        help="Nom du fichier CSV de sortie"
    )

    parser.add_argument(
        "-s",
        "--silences",
        default="playlist_tracks_with_silences.csv",
        help="Nom du fichier CSV de sortie avec silences"
    )

    parser.add_argument(
        "-j",
        "--json",
        default="playlist_tracks.json",
        help="Nom du fichier JSON de sortie"
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Ne pas afficher les morceaux dans le terminal"
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "Erreur : définis SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET dans le fichier .env ou dans les variables d'environnement.",
            file=sys.stderr,
        )
        return 1

    try:
        playlist_id = extract_playlist_id(args.playlist)
        token = get_access_token(client_id, client_secret)
        tracks = get_playlist_tracks(playlist_id, token)
        tracks_with_silences = insert_silence_between_tracks(tracks, SILENCE_TRACK)

        if not args.quiet:
            for track in tracks:
                print(track["filename"])

        #save_to_csv(tracks_with_silences, args.silences)
        save_with_silence_to_csv(tracks, args.silences)
        save_to_csv(tracks, args.csv)
        save_to_json(tracks, args.json)


        print(f"Total entrées : {len(tracks)}")
        print(f"CSV généré : {args.csv}")
        print(f"JSON généré : {args.json}")
        return 0

    except requests.HTTPError as e:
        print(f"Erreur HTTP Spotify : {e}", file=sys.stderr)
        return 2
    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())