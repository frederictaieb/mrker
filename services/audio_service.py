import numpy as np
import soundfile as sf
from pprint import pformat
from pathlib import Path
import subprocess


from utils.logger import get_logger

logger = get_logger(__name__)


class AudioService:

    INPUT_PATH = Path("data/input/input.wav")
    OUTPUT_DIR = Path("data/output")
    WAV_DIR = OUTPUT_DIR / "wav"
    FLAC_DIR = OUTPUT_DIR / "flac"
    MP3_DIR = OUTPUT_DIR / "mp3"

    def __init__(self):
        self.markers = []

    def _detect_markers(
        self,
        silence_threshold: float = 0.01,
        min_silence_ms: int = 300,
        min_track_ms: int = 1000,
    ) -> list[tuple[int, int]]:
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

    def _generate_wav(self, filenames):
        output_dir = self.WAV_DIR
        output_dir.mkdir(parents=True, exist_ok=True)
        created_files : list[str] = []

        for i, ((start_sec, end_sec), filename) in enumerate(zip(self.markers, filenames),start=1,):

            output_path = (output_dir / filename).with_suffix(".wav")

            logger.info(f"[{i}] Export WAV: "f"| {output_path.name}")

            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(self.INPUT_PATH),
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

    def _convert_wav_files(self, output_dir, extension, codec_args, label):
        input_wav_dir = Path(self.WAV_DIR)
        output_dir = Path(output_dir)

        output_dir.mkdir(parents=True, exist_ok=True)
        wav_files = sorted(input_wav_dir.glob("*.wav"))

        if not wav_files:
            logger.info("Aucun fichier WAV trouvé.")
            return []

        created_files = []

        for i, wav_path in enumerate(wav_files, start=1):
            output_path = (output_dir / wav_path.name).with_suffix(extension)

            logger.info(f"[{i}] Export {label}: | {output_path.name}")

            cmd = [
                "ffmpeg",
                "-y",
                "-i", str(wav_path),
                "-vn",
                *codec_args,
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

    def _generate_flac(self, filenames=None):
        return self._convert_wav_files(
            output_dir=self.FLAC_DIR,
            extension=".flac",
            codec_args=[
                "-c:a", "flac",
                "-compression_level", "8",
            ],
            label="FLAC",
        )

    def _generate_mp3(self, filenames=None):
        return self._convert_wav_files(
            output_dir=self.MP3_DIR,
            extension=".mp3",
            codec_args=[
                "-af", "loudnorm=I=-14:TP=-1.5:LRA=11",
                "-acodec", "libmp3lame",
                "-qscale:a", "0",
                "-joint_stereo", "1",
            ],
            label="MP3",
        )


    def generate_music(self, filenames):
        self._generate_wav(filenames)
        self._generate_flac(filenames)
        self._generate_mp3(filenames)

    @classmethod
    def create_with_detection(cls):
        obj = cls()
        obj._detect_markers()
        return obj

    def get_markers(self):
        return self.markers

    def count(self):
        return len(self.markers)

    def __str__(self):
        return f"{len(self.markers)} markers:\n{pformat(self.markers)}" 

    def __repr__(self):
        return f"AudioService(INPUT_PATH={self.INPUT_PATH!r}, markers={len(self.markers)})"