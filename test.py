import os
import argparse
from dotenv import load_dotenv
from services.spotify_services import SpotifyService
from services.audio_services import AudioService
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

print(sp_service)
print(as_service)

