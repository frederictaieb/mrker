import numpy as np
import soundfile as sf
from pprint import pformat
from pathlib import Path
import subprocess
from utils.file import delete_path
from datetime import datetime
from typing import Optional


from utils.logger import get_logger

logger = get_logger(__name__)


class AudioService:

    INPUT_PATH = Path("data/input/input.wav")
    OUTPUT_DIR = Path("data/output")
    WAV_DIR = OUTPUT_DIR / "wav"
    FLAC_DIR = OUTPUT_DIR / "flac"
    MP3_DIR = OUTPUT_DIR / "mp3"

    def __init__(self):
        self.markers: list[tuple[float, float]] = []

    def _detect_markers(
        self,
        silence_threshold: float = 0,
        min_silence_ms: int = 300,
        min_track_ms: int = 1000,
    ) -> list[tuple[float, float]]:
        data, sr = sf.read(self.INPUT_PATH)

        # passage en mono
        if data.ndim > 1:
            data = np.mean(data, axis=1)

        data = data.astype(np.float32)

        min_silence_samples = int(sr * min_silence_ms / 1000)
        min_track_samples = int(sr * min_track_ms / 1000)

        markers = []

        def is_silent(sample: float) -> bool:
            return abs(sample) <= silence_threshold

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
                        start_s = start_ms / 1000
                        end_s = end_ms / 1000
                        markers.append((start_s, end_s))

                    in_track = False
                    silence_run = 0

        # si le fichier se termine pendant une track
        if in_track:
            track_end = len(data)
            if track_end - track_start >= min_track_samples:
                start_ms = int(track_start * 1000 / sr)
                end_ms = int(track_end * 1000 / sr)
                start_s = start_ms / 1000
                end_s = end_ms / 1000
                markers.append((start_s, end_s))

        self.markers = markers
        return markers

    def _run_ffmpeg(
        self,
        input_path: Path,
        output_path: Path,
        metadata: Optional[dict] = None,
        codecs: Optional[list[str]] = None,
    ):
        logger.info(f"Export : | {output_path.name}")
        cmd = ["ffmpeg", "-y", "-i", str(input_path), "-vn",]

        if metadata:
            for key, value in metadata.items():
                cmd += ["-metadata", f"{key}={value}"]

        if codecs:
            cmd += codecs

        cmd.append(str(output_path))

        try:
            subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        except subprocess.CalledProcessError as e:
            logger.error(f"ffmpeg failed for {output_path}: {e.stderr}")
            raise



    def generate_tracks(self, tracks_data):
        output_dir = self.WAV_DIR
        output_dir.mkdir(parents=True, exist_ok=True)

        mp3_dir = self.MP3_DIR
        mp3_dir.mkdir(parents=True, exist_ok=True)

        flac_dir = self.FLAC_DIR
        flac_dir.mkdir(parents=True, exist_ok=True)

        if len(self.markers) != len(tracks_data):
            logger.error(self.markers)
            logger.error(tracks_data)
            raise ValueError(f"Mismatch: {len(self.markers)} markers but {len(tracks_data)} tracks data")


        for (start_sec, end_sec), track in zip(self.markers, tracks_data):
            filename = track["filename"]
            artist = track["artist"]
            title = track["title"]
            album = track["album"]
            created = datetime.now().strftime("%Y%m%d_%H%M%S")

            wav_path = (output_dir / filename).with_suffix(".wav")
            mp3_path = (mp3_dir / filename).with_suffix(".mp3")
            flac_path = (flac_dir / filename).with_suffix(".flac")
            
            self._run_ffmpeg(
                input_path=self.INPUT_PATH, 
                output_path=wav_path, 
                codecs=["-af", f"atrim=start={start_sec}:end={end_sec},asetpts=PTS-STARTPTS","-c:a", "pcm_s16le"]
            )

            self._run_ffmpeg(
                input_path=wav_path,
                output_path=flac_path,
                metadata={"artist": artist,"title": title,"album": album,"date": created,},
                codecs=["-c:a", "flac","-compression_level", "8",],
            )
            self._run_ffmpeg(
                input_path=wav_path,
                output_path=mp3_path,
                metadata={"artist": artist,"title": title,"album": album,"date": created,},
                codecs=["-af", "loudnorm=I=-14:TP=-1.5:LRA=11", "-acodec", "libmp3lame", "-qscale:a", "0", "-joint_stereo", "1",],
            )

            print("")

    def _reset(self):
        delete_path(self.WAV_DIR)
        delete_path(self.MP3_DIR)
        delete_path(self.FLAC_DIR)
        logger.info("WAV, MP3 and FLAC files from previous extract are erased")

    @classmethod
    def create_with_detection(cls):
        obj = cls()
        obj._reset()
        obj._detect_markers()
        return obj

    @classmethod
    def create_with_xls(cls, markers):
        obj = cls()
        obj._reset()
        obj.markers = markers
        return obj

    def get_markers(self):
        return self.markers

    def count(self):
        return len(self.markers)

    def __str__(self):
        return f"{len(self.markers)} markers:\n{pformat(self.markers)}" 

    def __repr__(self):
        return f"AudioService(INPUT_PATH={self.INPUT_PATH!r}, markers={len(self.markers)})"