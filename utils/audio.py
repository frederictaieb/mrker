from pathlib import Path
import subprocess


def split(
    tracks: list[dict],
    wav_filename: str,
    output_dir: str = "data/mp3",
    bitrate: str = "320k",
) -> list[str]:
    wav_path = Path(wav_filename)
    out_dir = Path(output_dir)

    if not wav_path.exists():
        raise FileNotFoundError(f"WAV introuvable : {wav_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []
    current_time = 0.0
    total_tracks = len(tracks)

    for i, track in enumerate(tracks, start=1):
        duration_ms = track["duration_ms"]
        duration_sec = duration_ms / 1000.0
        output_path = out_dir / track["filename"]

        print(f"[{i}/{total_tracks}] Export : {track['artist']} - {track['title']}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(wav_path),
            "-ss", str(current_time),
            "-t", str(duration_sec),
            "-vn",
            "-acodec", "libmp3lame",
            "-b:a", bitrate,
            "-id3v2_version", "3",
            "-metadata", f"title={track['title']}",
            "-metadata", f"artist={track['artist']}",
            "-metadata", f"album={track['album']}",
            "-metadata", f"track={i}/{total_tracks}",
            str(output_path),
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        created_files.append(str(output_path))
        current_time += duration_sec

    return created_files