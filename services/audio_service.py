import numpy as np
import soundfile as sf
from pprint import pformat


class AudioService:
    def __init__(self, audio_filename: str = "data/input/input.wav"):
        self.audio_filename = audio_filename
        self.markers = []

    def _detect_markers(
        self,
        silence_threshold: float = 0.01,
        min_silence_ms: int = 300,
        min_track_ms: int = 1000,
    ) -> list[tuple[int, int]]:
        data, sr = sf.read(self.audio_filename)

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
                        markers.append((start_ms, end_ms))

                    in_track = False
                    silence_run = 0

        # si le fichier se termine pendant une track
        if in_track:
            track_end = len(data)
            if track_end - track_start >= min_track_samples:
                start_ms = int(track_start * 1000 / sr)
                end_ms = int(track_end * 1000 / sr)
                markers.append((start_ms, end_ms))

        self.markers = markers
        return markers

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
        return f"AudioService(audio_filename={self.audio_filename!r}, markers={len(self.markers)})"