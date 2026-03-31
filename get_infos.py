import os
import sys
import json
import argparse
from pathlib import Path

from dotenv import load_dotenv

from utils.spotify import get_tracks
from utils.tools import delete_path
from utils.audio import detect_tracks, save_to_labels, save_to_json, extract_wav, generate_mp3, generate_flac

from openpyxl import Workbook

load_dotenv()

CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

JSON_FILE = os.environ.get("JSON_FILE")
EXCEL_FILE = os.environ.get("EXCEL_FILE")

def clean():
    delete_path(JSON_FILE)
    delete_path(EXCEL_FILE)
    delete_path(OUTPUT_WAV_DIR)
    delete_path(OUTPUT_MP3_DIR)
    delete_path(OUTPUT_FLAC_DIR)

def get_info():
    clean()

generate_xls():
    wb = Workbook()
    ws = wb.active
    ws.title = "MaFeuille"



def main() -> int:
    # Get ARGS: Playlist URL
    parser = argparse.ArgumentParser(description="Split WAV based on silence + Spotify playlist")
    parser.add_argument("playlist", help="URL ou ID de la playlist Spotify")
    args = parser.parse_args()

    try:
        
        print(f"Recovering Data ...")
        tracks = get_tracks(client_id, client_secret, args.playlist)
        filenames = [track["filename"] for track in tracks]
        save_to_json(tracks, JSON_FILE)
        print(f"- {filenames}")
        nb_tracks = filenames
        print(f"Count tracks : {nb_tracks}")

        print(f"Detecting Silences")
        detections = detect_tracks(INPUT_FILE)
        save_to_labels(detections, LABEL_FILE)
        print(f"- {nb_silences}")
        print(f"Count time sections : {nb_silences}")

        generate_xls()

        if nb_silences == nb_tracks:
            

        print("Extracting WAV")
        extract_wav(
            input_filename=INPUT_FILE,
            timestamps=detections,
            filenames=filenames,
            output_dir=OUTPUT_WAV_DIR,
        )

        print("Generating MP3")
        generate_mp3(OUTPUT_WAV_DIR, OUTPUT_MP3_DIR)

        print("Generating FLAC")
        generate_flac(OUTPUT_WAV_DIR, OUTPUT_FLAC_DIR)

        return 0

    except Exception as e:
        print(f"Erreur : {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())