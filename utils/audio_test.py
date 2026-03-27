from pathlib import Path
import subprocess
import shutil
import numpy as np
import soundfile as sf

from utils.tools import ms_to_hms_dcm


def detect_tracks_from_silence(
    input_filename: str,
    silence_threshold: float = 0.0,
    min_silence_ms: int = 300,
    min_track_ms: int = 1000,
) -> list[tuple[int, int]]:
    """
    Détecte les tracks dans un WAV à partir des silences.

    Retourne une liste de tuples :
        [(start_ms, end_ms), ...]

    Logique :
    - silence tant que abs(sample) <= silence_threshold
    - début de track au premier sample non silencieux
    - fin de track lorsqu'on rencontre un silence d'au moins min_silence_ms
    """

    data, sr = sf.read(input_filename)

    # passage en mono
    if data.ndim > 1:
        data = np.mean(data, axis=1)

    data = data.astype(np.float32)

    min_silence_samples = int(sr * min_silence_ms / 1000)
    min_track_samples = int(sr * min_track_ms / 1000)

    def is_silent(sample: float) -> bool:
        return abs(sample) <= silence_threshold

    tracks: list[tuple[int, int]] = []

    in_track = False
    track_start = 0
    silence_run = 0

    for i, sample in enumerate(data):
        if is_silent(sample):
            silence_run += 1
        else:
            silence_run = 0

        if not in_track:
            if not is_silent(sample):
                in_track = True
                track_start = i
                silence_run = 0
        else:
            if silence_run >= min_silence_samples:
                track_end = i - silence_run + 1

                if track_end - track_start >= min_track_samples:
                    start_ms = int(track_start * 1000 / sr)
                    end_ms = int(track_end * 1000 / sr)
                    #print (f"{ms_to_hms_dcm(start_ms)} {ms_to_hms_dcm(end_ms)}")
                    tracks.append((start_ms, end_ms))

                in_track = False
                silence_run = 0

    # si le fichier se termine pendant une track
    if in_track:
        track_end = len(data)
        if track_end - track_start >= min_track_samples:
            start_ms = int(track_start * 1000 / sr)
            end_ms = int(track_end * 1000 / sr)
            tracks.append((start_ms, end_ms))

    return tracks

def split_wav_from_ranges(
    input_filename: str,
    ranges_ms: list[tuple[int, int]],
    output_dir: str = "data/output/wav",
) -> list[str]:
    input_path = Path(input_filename)
    out_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Fichier audio introuvable : {input_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []

    for i, (start_ms, end_ms) in enumerate(ranges_ms, start=1):
        if start_ms < 0 or end_ms <= start_ms:
            print(f"[SKIP {i}] plage invalide : ({start_ms}, {end_ms})")
            continue

        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0

        output_path = out_dir / f"{i}.wav"

        print(f"[{i}] Export : {ms_to_hms_dcm(start_ms)} -> {ms_to_hms_dcm(end_ms)} ms | {output_path.name}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(input_path),
            "-vn",
            "-af", f"atrim=start={start_sec}:end={end_sec},asetpts=PTS-STARTPTS",
            "-c:a", "pcm_s16le",
            str(output_path),
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        created_files.append(str(output_path))

    return created_files