# main.py
import os
import sys
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv

from utils.spotify import get_tracks

from utils.audio import split


load_dotenv()


def save_to_json(tracks: list[dict], filename: str) -> None:
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Récupère les morceaux d'une playlist Spotify, génère un JSON et découpe un WAV en MP3."
    )

    parser.add_argument(
        "playlist",
        help="URL de la playlist Spotify"
    )

    parser.add_argument(
        "-j",
        "--json",
        default="data/infos/playlist_tracks.json",
        help="Fichier JSON de sortie",
    )

    parser.add_argument(
        "-w",
        "--wav",
        default="data/input/input.wav",
        help="Chemin vers le fichier WAV à découper",
    )

    parser.add_argument(
        "-o",
        "--output-dir",
        default="data/output",
        help="Dossier de sortie des MP3",
    )

    parser.add_argument(
        "-b",
        "--bitrate",
        default="320k",
        help="Bitrate MP3 (ex: 192k, 320k)",
    )

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "Erreur : définis SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET dans le .env",
            file=sys.stderr,
        )
        return 1

    try:

        tracks = get_tracks(client_id, client_secret, args.playlist)

        # 💾 JSON
        save_to_json(tracks, args.json)
        print(f"JSON généré : {args.json}")

        # 🎚 Découpage WAV → MP3
        if args.wav:
            print("Découpage du WAV en cours...")

            files = split(
                tracks=tracks,
                wav_filename=args.wav,
                output_dir=args.output_dir,
                bitrate=args.bitrate,
            )

            print(f"MP3 générés : {len(files)}")
            print(f"Dossier : {args.output_dir}")

        return 0

    except requests.HTTPError as e:
        print(f"Erreur HTTP Spotify : {e}", file=sys.stderr)
        return 2

    except FileNotFoundError as e:
        print(f"Fichier introuvable : {e}", file=sys.stderr)
        return 3

    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())