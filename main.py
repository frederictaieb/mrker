import os
import sys
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv

from utils.spotify import get_tracks
from utils.audio import detect_tracks, extract_wav, generate_mp3, generate_flac


load_dotenv()


def save_to_json(tracks: list[dict], filename: str) -> None:
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

    print(f"JSON généré : {filename}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Split WAV based on silence + Spotify playlist")
    parser.add_argument("playlist", help="URL ou ID de la playlist Spotify")

    args = parser.parse_args()

    INPUT_FILE = "data/input/input.wav"
    JSON_FILE = "data/output/tracks.json"

    OUTPUT_WAV_DIR = "data/output/wav"
    OUTPUT_MP3_DIR = "data/output/mp3"
    OUTPUT_FLAC_DIR = "data/output/FLAC"

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
        filenames = [track["filename"] for track in tracks]
        detections = detect_tracks(INPUT_FILE)
        save_to_json(tracks, JSON_FILE)

        extract_wav(
            input_filename=INPUT_FILE,
            timestamps=detections,
            filenames=filenames,
            output_dir=OUTPUT_WAV_DIR,
        )

        generate_mp3(OUTPUT_WAV_DIR, OUTPUT_MP3_DIR)
        generate_flac(OUTPUT_WAV_DIR, OUTPUT_FLAC_DIR)

        return 0

    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())