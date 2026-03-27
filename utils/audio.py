from pathlib import Path
from utils.tools import format_duration_ms
import subprocess
import numpy as np
import soundfile as sf
import shutil


# =========================
# CUT DETECTION
# =========================

def find_best_cut_with_moving_average(
    signal: np.ndarray,
    sr: int,
    theoretical_cut_ms: int,
    window_ms: int = 2000,
    average_window_ms: int = 100,
) -> int:
    half_window_ms = window_ms // 2

    search_start_ms = max(0, theoretical_cut_ms - half_window_ms)
    search_end_ms = theoretical_cut_ms + half_window_ms

    avg_window_samples = max(1, int(sr * average_window_ms / 1000))
    ms_step_samples = max(1, int(sr / 1000))

    search_start_sample = int(search_start_ms * sr / 1000)
    search_end_sample = int(search_end_ms * sr / 1000)

    best_cut_sample = search_start_sample
    best_avg = None

    current_sample = search_start_sample

    while (
        current_sample + avg_window_samples <= len(signal)
        and current_sample <= search_end_sample
    ):
        window = signal[current_sample:current_sample + avg_window_samples]
        avg_volume = float(np.mean(np.abs(window)))

        if best_avg is None or avg_volume < best_avg:
            best_avg = avg_volume
            best_cut_sample = current_sample

        current_sample += ms_step_samples

    return int(best_cut_sample * 1000 / sr)


def compute_cut_points_iterative(
    tracks: list[dict],
    input_filename: str,
    search_window_ms: int = 2000,
    average_window_ms: int = 100,
) -> list[int]:
    data, sr = sf.read(input_filename)

    if data.ndim > 1:
        data = data.mean(axis=1)

    data = data.astype(np.float32)

    cut_points = [0]
    current_cut_ms = 0

    for i, track in enumerate(tracks[:-1], start=1):
        theoretical_cut_ms = current_cut_ms + int(track["duration_ms"])

        adjusted_cut_ms = find_best_cut_with_moving_average(
            signal=data,
            sr=sr,
            theoretical_cut_ms=theoretical_cut_ms,
            window_ms=search_window_ms,
            average_window_ms=average_window_ms,
        )

        print(
            f"[CUT {i}] "
            f"{format_duration_ms(theoretical_cut_ms)} -> "
            f"{format_duration_ms(adjusted_cut_ms)} "
            f"(delta={adjusted_cut_ms - theoretical_cut_ms} ms)"
        )

        cut_points.append(adjusted_cut_ms)
        current_cut_ms = adjusted_cut_ms

    total_duration_ms = int(len(data) * 1000 / sr)
    cut_points.append(total_duration_ms)

    return cut_points


# =========================
# SPLIT WAV
# =========================

def split(
    tracks: list[dict],
    input_filename: str,
    output_dir: str = "data/output/wav",
) -> list[str]:
    input_path = Path(input_filename)
    out_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Fichier audio introuvable : {input_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    cut_points_ms = compute_cut_points_iterative(tracks, str(input_path))

    created_files: list[str] = []
    total_tracks = len(tracks)

    for i, track in enumerate(tracks, start=1):
        start_ms = cut_points_ms[i - 1]
        end_ms = cut_points_ms[i]

        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0

        final_output_path = (out_dir / track["filename"]).with_suffix(".wav")

        print(
            f"[{i}/{total_tracks}] Export WAV : "
            f"[{format_duration_ms(start_ms)} - {format_duration_ms(end_ms)}] - "
            f"{track['artist']} - {track['title']}"
        )

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-af", f"atrim=start={start_sec}:end={end_sec},asetpts=PTS-STARTPTS",
            "-c:a", "pcm_s16le",
            str(final_output_path),
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        created_files.append(str(final_output_path))

    return created_files


# =========================
# METADATA HELPERS
# =========================

def build_common_metadata_args(
    track: dict,
    track_number: int,
    total_tracks: int,
) -> list[str]:
    metadata_args = [
        "-metadata", f"title={track.get('title', '')}",
        "-metadata", f"artist={track.get('artist', '')}",
        "-metadata", f"album={track.get('album', '')}",
        "-metadata", f"track={track_number}/{total_tracks}",
    ]

    if track.get("date"):
        metadata_args += ["-metadata", f"date={track['date']}"]

    if track.get("genre"):
        metadata_args += ["-metadata", f"genre={track['genre']}"]

    return metadata_args


# =========================
# CONVERT MP3
# =========================

def convert_wav_to_mp3(
    wav_path: str,
    mp3_path: str,
    track: dict,
    track_number: int,
    total_tracks: int,
    normalize: bool = True,
):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", wav_path,
        "-vn",
    ]

    if normalize:
        cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]

    cmd += [
        "-acodec", "libmp3lame",
        "-qscale:a", "0",
        "-joint_stereo", "1",
        "-id3v2_version", "3",
        "-write_id3v1", "1",
    ]

    cmd += build_common_metadata_args(track, track_number, total_tracks)
    cmd += [mp3_path]

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def convert_all_to_mp3(
    wav_files: list[str],
    tracks: list[dict],
    output_dir: str = "data/output/mp3",
    normalize: bool = True,
) -> list[str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_tracks = len(tracks)
    mp3_files: list[str] = []

    for i, (wav_file, track) in enumerate(zip(wav_files, tracks), start=1):
        mp3_path = out_dir / Path(wav_file).with_suffix(".mp3").name

        print(f"[MP3 {i}/{total_tracks}] {track['artist']} - {track['title']}")

        convert_wav_to_mp3(
            wav_path=wav_file,
            mp3_path=str(mp3_path),
            track=track,
            track_number=i,
            total_tracks=total_tracks,
            normalize=normalize,
        )

        mp3_files.append(str(mp3_path))

    return mp3_files


# =========================
# CONVERT FLAC
# =========================

def convert_wav_to_flac(
    wav_path: str,
    flac_path: str,
    track: dict,
    track_number: int,
    total_tracks: int,
):
    cmd = [
        "ffmpeg",
        "-y",
        "-i", wav_path,
        "-vn",
        "-c:a", "flac",
        "-compression_level", "8",
    ]

    cmd += build_common_metadata_args(track, track_number, total_tracks)
    cmd += [flac_path]

    subprocess.run(
        cmd,
        check=True,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )


def convert_all_to_flac(
    wav_files: list[str],
    tracks: list[dict],
    output_dir: str = "data/output/flac",
) -> list[str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    total_tracks = len(tracks)
    flac_files: list[str] = []

    for i, (wav_file, track) in enumerate(zip(wav_files, tracks), start=1):
        flac_path = out_dir / Path(wav_file).with_suffix(".flac").name

        print(f"[FLAC {i}/{total_tracks}] {track['artist']} - {track['title']}")

        convert_wav_to_flac(
            wav_path=wav_file,
            flac_path=str(flac_path),
            track=track,
            track_number=i,
            total_tracks=total_tracks,
        )

        flac_files.append(str(flac_path))

    return flac_files


# =========================
# FULL PIPELINE
# =========================

def process_mix(
    tracks: list[dict],
    input_file: str,
    wav_output_dir: str = "data/output/wav",
    mp3_output_dir: str = "data/output/mp3",
    flac_output_dir: str = "data/output/flac",
    generate_mp3: bool = True,
    generate_flac: bool = True,
    normalize_mp3: bool = True,
) -> dict[str, list[str]]:

    wav_files = split(
        tracks=tracks,
        input_filename=input_file,
        output_dir=wav_output_dir,
    )

    result: dict[str, list[str]] = {
        "wav": wav_files,
        "mp3": [],
        "flac": [],
    }

    if generate_mp3:
        result["mp3"] = convert_all_to_mp3(
            wav_files=wav_files,
            tracks=tracks,
            output_dir=mp3_output_dir,
            normalize=normalize_mp3,
        )

    if generate_flac:
        result["flac"] = convert_all_to_flac(
            wav_files=wav_files,
            tracks=tracks,
            output_dir=flac_output_dir,
        )

    return result

    import shutil
from pathlib import Path


def clean_output_dirs(dirs: list[str]) -> None:
    for d in dirs:
        path = Path(d)

        if path.exists():
            shutil.rmtree(path)  # 🔥 supprime tout le dossier

        path.mkdir(parents=True, exist_ok=True)  # recrée propre

        print(f"Dossier nettoyé : {path}")