#utils/spotify.py

import base64
import requests
from urllib.parse import urlparse


from utils.tools import format_duration_ms
from utils.text import clean_album, clean_title, build_filename

class SpotifyAccess :
    def __init__(self, client_id, client_secret, playlist_url):
        self.client_id = client_id 
        self.client_secret = client_secret
        self.playlist_url = playlist_url

    def _get_access_token():
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
        return response.json()["access_token"]

    def parse_playlist_id(playlist_url: str) -> str:
        path = urlparse(playlist_url).path
        parts = [p for p in path.split("/") if p]
        if len(parts) >= 2 and parts[0] == "playlist":
            return parts[1]
        raise ValueError("URL de playlist Spotify invalide")
    
    get_tracks():
        playlist_id = self.parse_playlist_id(playlist)
        token = self.get_access_token(client_id, client_secret)
        return 1
        #return get_playlist_tracks(playlist_id, token)

@classmethod
def create_with_tracks(cls, client_id, client_secret, playlist_url):
    obj = cls(client_id, client_secret, playlist_url)
    obj.retrieve()
    return obj

def _get_access_token(client_id: str, client_secret: str) -> str:
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
