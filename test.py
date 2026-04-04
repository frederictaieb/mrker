import os
import argparse
from dotenv import load_dotenv
from services.spotify_service import SpotifyService
from services.audio_service import AudioService
from services.xls_service import XlsService
from utils.logger import get_logger

logger = get_logger(__name__)

if XlsService.is_generated():
    logger.info("XLS File detected.")
    logger.info("Getting Data from XLS file...")
    tracks_data, markers = XlsService.load()
    logger.info("XLS Service and Audio Service created from File")
    xls_service = XlsService(markers=markers, tracks_data=tracks_data)
    as_service = AudioService.create_with_xls(markers)

    if xls_service.same_len():
        logger.info(f"Counts of Filenames and Marker are the same.")
        logger.info(f"Generating WAV, FLAC and MP3 from XLS file...")
        as_service.generate_tracks(tracks_data)
        xls_service.reset()
    else:
       logger.error("Counts of tracks and markers from XLS file are different.")
       logger.error("Exiting program")
       raise SystemExit(1)

else: 

    load_dotenv()

    SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
    SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

    parser = argparse.ArgumentParser(description="Split WAV based on silence + Spotify playlist")
    parser.add_argument("playlist", help="URL ou ID de la playlist Spotify")
    args = parser.parse_args()

    logger.info("Creating Spotify Service from pasted URL")
    sp_service = SpotifyService.create_with_data(
        SPOTIFY_CLIENT_ID, 
        SPOTIFY_CLIENT_SECRET,
        args.playlist
    )

    logger.info("Creating Audio Service")
    tracks_data = sp_service.get_tracks_data()
    as_service = AudioService.create_with_detection()

    logger.info("Creating XLS Service")
    xls_service = XlsService(
        markers = as_service.get_markers(),
        tracks_data = tracks_data
    )

    if xls_service.same_len():
        logger.info(f"Counts of Filenames and Marker are the same.")
        logger.info(f"Generating WAV, FLAC and MP3...")
        as_service.generate_tracks(tracks_data)
        xls_service.reset()
    else:
        xls_service.generate()
        logger.info(f"Counts of Filenames and Markers are different.")
        logger.info(f"XLS file generated.")




