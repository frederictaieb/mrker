from pathlib import Path
import subprocess
import shutil
import numpy as np
import soundfile as sf

import json
import datetime

from datetime import datetime

from utils.tools import ms_to_hms_dcm

from mutagen.id3 import ID3, TIT2, TPE1, TALB, TDRC, COMM, TXXX


def load_metadata_map(json_path: str) -> dict[str, dict]:
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    metadata_map = {}
    for item in data:
        filename = item.get("filename")
        if filename:
            metadata_map[filename] = item

    return metadata_map

def write_mp3_metadata(
    mp3_path: str,
    artist: str | None = None,
    album: str | None = None,
    title: str | None = None,
    spotify_link: str | None = None,
    created_at: str | None = None,
) -> None:
    if created_at is None:
        created_at = datetime.now().isoformat(timespec="seconds")

    mp3_file = Path(mp3_path)

    try:
        tags = ID3(mp3_file)
    except Exception:
        tags = ID3()

    # On remplace proprement les champs standards
    tags.delall("TIT2")
    tags.delall("TPE1")
    tags.delall("TALB")
    tags.delall("TDRC")

    # On nettoie les champs custom qu'on gère nous-mêmes
    tags.delall("COMM")
    tags.delall("TXXX")

    if title:
        tags.add(TIT2(encoding=3, text=title))

    if artist:
        tags.add(TPE1(encoding=3, text=artist))

    if album:
        tags.add(TALB(encoding=3, text=album))

    # Date/heure de création
    tags.add(TDRC(encoding=3, text=created_at))

    tags.add(COMM(
        encoding=3,
        lang="eng",
        desc="creation_time",
        text=f"Created at {created_at}"
    ))

    tags.add(TXXX(
        encoding=3,
        desc="CREATED_TIMESTAMP",
        text=created_at
    ))

    if spotify_link:
        tags.add(TXXX(
            encoding=3,
            desc="SPOTIFY_LINK",
            text=spotify_link
        ))

    tags.save(mp3_file)

def save_to_json(tracks: list[dict], filename: str) -> None:
    output_path = Path(filename)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(tracks, f, ensure_ascii=False, indent=2)

    print(f"JSON généré : {filename}")

def save_to_labels(
    tracks: list[tuple[int, int]],
    output_filename: str,
    prefix: str = "Track"
) -> None:
    out_path = Path(output_filename)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    with open(out_path, "w", encoding="utf-8") as f:
        for i, (start_ms, end_ms) in enumerate(tracks, start=1):
            start_s = start_ms / 1000
            end_s = end_ms / 1000
            label = f"{prefix} {i}"
            f.write(f"{start_s:.3f}\t{end_s:.3f}\t{label}\n")
    print(f"Labels txt généré : {filename}")


def detect_tracks(
    input_filename: str,
    silence_threshold: float = 0.0,
    min_silence_ms: int = 300,
    min_track_ms: int = 1000,
    audacity_labels_output: str | None = None,
) -> list[tuple[int, int]]:
    """
    Détecte les tracks dans un WAV à partir des silences.

    Retourne une liste de tuples :
        [(start_ms, end_ms), ...]

    Logique :
    - silence tant que abs(sample) <= silence_threshold
    - début de track au premier sample non silencieux
    - fin de track lorsqu'on rencontre un silence d'au moins min_silence_ms

    Si audacity_labels_output est renseigné, exporte aussi un fichier
    de labels importable dans Audacity.
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

    if audacity_labels_output:
        export_audacity_labels(tracks, audacity_labels_output)

    print(tracks)
    return tracks

def extract_wav(
    input_filename: str,
    timestamps: list[tuple[int, int]],
    filenames: list[str],
    output_dir: str = "data/output/wav",
) -> list[str]:
    input_path = Path(input_filename)
    out_dir = Path(output_dir)

    if not input_path.exists():
        raise FileNotFoundError(f"Fichier audio introuvable : {input_path}")

    if len(filenames) != len(timestamps):
        raise ValueError(
            "filenames doit contenir autant d'éléments que timestamps"
        )

    out_dir.mkdir(parents=True, exist_ok=True)

    created_files: list[str] = []

    for i, ((start_ms, end_ms), filename) in enumerate(
        zip(timestamps, filenames),
        start=1,
    ):
        if start_ms < 0 or end_ms <= start_ms:
            print(f"[SKIP {i}] plage invalide : ({start_ms}, {end_ms})")
            continue

        start_sec = start_ms / 1000.0
        end_sec = end_ms / 1000.0

        output_path = (out_dir / filename).with_suffix(".wav")

        print(
            f"[{i}] Export : "
            f"{ms_to_hms_dcm(start_ms)} -> {ms_to_hms_dcm(end_ms)} "
            f"| {output_path.name}"
        )

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

def generate_mp3(
    input_wav_dir: str,
    output_mp3_dir: str,
    metadata_json_path: str = "data/output/tracks.json",
    normalize: bool = True,
) -> list[str]:
    in_dir = Path(input_wav_dir)
    out_dir = Path(output_mp3_dir)
    json_path = Path(metadata_json_path)

    if not in_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable : {in_dir}")

    if not json_path.exists():
        raise FileNotFoundError(f"Fichier JSON introuvable : {json_path}")

    out_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(in_dir.glob("*.wav"))

    if not wav_files:
        print("Aucun fichier WAV trouvé.")
        return []

    metadata_map = load_metadata_map(str(json_path))
    created_files = []

    for i, wav_path in enumerate(wav_files, start=1):
        mp3_path = (out_dir / wav_path.name).with_suffix(".mp3")

        print(f"[MP3 {i}/{len(wav_files)}] {wav_path.name}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(wav_path),
            "-vn",
        ]

        if normalize:
            cmd += ["-af", "loudnorm=I=-14:TP=-1.5:LRA=11"]

        cmd += [
            "-acodec", "libmp3lame",
            "-qscale:a", "0",
            "-joint_stereo", "1",
            str(mp3_path),
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        meta = metadata_map.get(wav_path.name)

        if meta is None:
            print(f"  -> métadonnées non trouvées pour : {wav_path.name}")
        else:
            write_mp3_metadata(
                mp3_path=str(mp3_path),
                artist=meta.get("artist"),
                album=meta.get("album"),
                title=meta.get("title"),
                spotify_link=meta.get("spotify_link"),
            )

        created_files.append(str(mp3_path))

    return created_files


def generate_flac(
    input_wav_dir: str,
    output_flac_dir: str,
) -> list[str]:
    in_dir = Path(input_wav_dir)
    out_dir = Path(output_flac_dir)

    if not in_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable : {in_dir}")

    out_dir.mkdir(parents=True, exist_ok=True)

    wav_files = sorted(in_dir.glob("*.wav"))

    if not wav_files:
        print("Aucun fichier WAV trouvé.")
        return []

    created_files = []

    for i, wav_path in enumerate(wav_files, start=1):
        flac_path = (out_dir / wav_path.name).with_suffix(".flac")

        print(f"[FLAC {i}/{len(wav_files)}] {wav_path.name}")

        cmd = [
            "ffmpeg",
            "-y",
            "-i", str(wav_path),
            "-vn",
            "-c:a", "flac",
            "-compression_level", "8",  # max compression sans perte
            str(flac_path),
        ]

        subprocess.run(
            cmd,
            check=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )

        created_files.append(str(flac_path))

    return created_files