import os
import argparse
from dotenv import load_dotenv
from services.spotify_service import SpotifyService
from services.audio_service import AudioService
from services.xls_service import XlsService
from utils.logger import get_logger

logger = get_logger(__name__)

load_dotenv()
SPOTIFY_CLIENT_ID = os.environ.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = os.environ.get("SPOTIFY_CLIENT_SECRET")

parser = argparse.ArgumentParser(description="Split WAV based on silence + Spotify playlist")
parser.add_argument("playlist", help="URL ou ID de la playlist Spotify")
args = parser.parse_args()

sp_service = SpotifyService.create_with_tracks(
    SPOTIFY_CLIENT_ID, 
    SPOTIFY_CLIENT_SECRET,
    args.playlist
)

as_service = AudioService.create_with_detection()

xls_service = XlsService.create(
    xls_file = "data/infos/makers.xls",
    txt_file = "data/infos/makers.txt",
    markers = as_service.get_markers(),
    filenames = sp_service.get_filenames()
)

print(sp_service)
print(as_service)

