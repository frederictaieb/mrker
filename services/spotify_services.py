import base64
import requests
from urllib.parse import urlparse

from utils.tools import format_duration_ms
from utils.text import clean_album, clean_title, build_filename

from pprint import pformat

from utils.logger import get_logger

logger = get_logger(__name__)

class SpotifyService:
    def __init__(self, client_id, client_secret, playlist_url):
        self.client_id = client_id
        self.client_secret = client_secret
        self.playlist_url = playlist_url
        self.playlist_id = None
        self.access_token = None
        self.tracks = []
        

    def _get_access_token(self):
        if self.access_token:
            return self.access_token

        logger.info("Getting access token from Spotify...")
        auth_string = f"{self.client_id}:{self.client_secret}"
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
        self.access_token = response.json()["access_token"]
        return self.access_token

    def _parse_playlist_id(self) -> str:
        if self.playlist_id:
            return self.playlist_id

        logger.info("Parsing URL to get playlist ID...")
        path = urlparse(self.playlist_url).path
        parts = [p for p in path.split("/") if p]

        if len(parts) >= 2 and parts[0] == "playlist":
            self.playlist_id = parts[1]
            return self.playlist_id

        raise ValueError("URL de playlist Spotify invalide")


    def _get_playlist_tracks(self) -> list[dict]:
        tracks = []
        url = f"https://api.spotify.com/v1/playlists/{self._parse_playlist_id()}/tracks"
        headers = {"Authorization": f"Bearer {self._get_access_token()}"}

        params = {
            "limit": 100,
            "fields": (
                "items(track(name,duration_ms,external_urls,album(name),artists(name),is_local)),"
                "next"
            )
        }

        while url:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            for item in data.get("items", []):
                track = item.get("track")
                if not track or track.get("is_local"):
                    continue

                artists = ", ".join(artist["name"] for artist in track.get("artists", []))
                raw_title = track.get("name", "")
                raw_album = track.get("album", {}).get("name", "")
                spotify_link = track.get("external_urls", {}).get("spotify", "")
                duration_ms = track.get("duration_ms", 0)
                duration = format_duration_ms(duration_ms)

                album = clean_album(raw_album)
                title = clean_title(raw_title, raw_album)
                filename = build_filename(artists, album, title)

                tracks.append({
                    "artist": artists,
                    "title": title,
                    "album": album,
                    "spotify_link": spotify_link,
                    "duration_ms": duration_ms,
                    "duration": duration,
                    "filename": filename,
                })

            url = data.get("next")
            params = None

        return tracks


    def _retrieve(self):
        self.tracks = self._get_playlist_tracks()
        return self.tracks

    def get_filenames(self):
        if not self.tracks:
            self._retrieve()
        return [track["filename"] for track in self.tracks]

    @classmethod
    def create_with_tracks(cls, client_id, client_secret, playlist_url):
        obj = cls(client_id, client_secret, playlist_url)
        obj._retrieve()
        return obj

    def count(self):
        return(len(filenames))

    def __str__(self):
        filenames = [track["filename"] for track in self.tracks]
        return f"{len(filenames)} tracks:\n{pformat(filenames)}"


    def __repr__(self):
        return f"SpotifyService(playlist_url={self.playlist_url!r}, tracks={len(self.tracks)})"
    