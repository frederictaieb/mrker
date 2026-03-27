# main.py
import os
import sys
import json
import argparse
from pathlib import Path

import requests
from dotenv import load_dotenv

from utils.spotify import get_tracks
from utils.audio import process_mix, clean_output_dirs

from utils.audio_test import detect_tracks_from_silence, split_wav_from_ranges


load_dotenv()


def save_to_json(tracks: list[dict], filename: str) -> None:
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

    print(f"JSON généré : {filename}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Récupère les morceaux d'une playlist Spotify, génère un JSON, découpe un WAV, puis exporte en MP3 et FLAC."
    )

    parser.add_argument("playlist", help="URL de la playlist Spotify")

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
        help="Chemin vers le fichier audio à découper",
    )

    parser.add_argument(
        "--wav-output-dir",
        default="data/output/wav",
        help="Dossier de sortie des WAV découpés",
    )

    parser.add_argument(
        "--mp3-output-dir",
        default="data/output/mp3",
        help="Dossier de sortie des MP3",
    )

    parser.add_argument(
        "--flac-output-dir",
        default="data/output/flac",
        help="Dossier de sortie des FLAC",
    )

    parser.add_argument(
        "--no-mp3",
        action="store_true",
        help="Ne pas générer les MP3",
    )

    parser.add_argument(
        "--no-flac",
        action="store_true",
        help="Ne pas générer les FLAC",
    )

    parser.add_argument(
        "--no-normalize-mp3",
        action="store_true",
        help="Ne pas normaliser les MP3",
    )

    return parser.parse_args()


def main() -> int:

    INPUT_FILE = "data/input/input.wav"
    OUTPUT_WAV_DIR = "data/output/wav"
    detections = detect_tracks_from_silence(INPUT_FILE)
    split_wav_from_ranges(INPUT_FILE, detections, OUTPUT_WAV_DIR)
    print (detections)
    #args = parse_args()

    #client_id = os.environ.get("SPOTIFY_CLIENT_ID")
    #client_secret = os.environ.get("SPOTIFY_CLIENT_SECRET")

    #if not client_id or not client_secret:
    #    print(
    #        "Erreur : définis SPOTIFY_CLIENT_ID et SPOTIFY_CLIENT_SECRET dans le .env",
    #        file=sys.stderr,
    #    )
    #    return 1

    #try:
    #    tracks = get_tracks(client_id, client_secret, args.playlist)
    #    save_to_json(tracks, args.json)

    #    if args.wav:
    #        print("Nettoyage des dossiers de sortie...")

    #        clean_output_dirs([
    #            args.wav_output_dir,
    #            args.mp3_output_dir,
    #            args.flac_output_dir,
    #        ])
            
    #        print("Découpage du WAV et export en cours...")

    #        result = process_mix(
    #            tracks=tracks,
    #            input_file=args.wav,
    #            wav_output_dir=args.wav_output_dir,
    #            mp3_output_dir=args.mp3_output_dir,
    #            flac_output_dir=args.flac_output_dir,
    #            generate_mp3=not args.no_mp3,
    #            generate_flac=not args.no_flac,
    #            normalize_mp3=not args.no_normalize_mp3,
    #        )

    #        print(f"WAV générés : {len(result['wav'])}")
    #        print(f"Dossier WAV : {args.wav_output_dir}")

    #        if not args.no_mp3:
    #            print(f"MP3 générés : {len(result['mp3'])}")
    #            print(f"Dossier MP3 : {args.mp3_output_dir}")

    #        if not args.no_flac:
    #            print(f"FLAC générés : {len(result['flac'])}")
    #            print(f"Dossier FLAC : {args.flac_output_dir}")

    #    return 0

    #except requests.HTTPError as e:
    #    print(f"Erreur HTTP Spotify : {e}", file=sys.stderr)
    #    return 2

    #except FileNotFoundError as e:
    #    print(f"Fichier introuvable : {e}", file=sys.stderr)
    #    return 3

    #except Exception as e:
    #    print(f"Erreur : {e}", file=sys.stderr)
    #    return 4


if __name__ == "__main__":
    raise SystemExit(main())