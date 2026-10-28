import numpy as np


class AudioAnalyzer:
    """Noise level (dB), speech-vs-silence ratio and activity pattern from raw audio."""

    def __init__(self, sample_rate=16000):
        self.sample_rate = sample_rate

    def _frames(self, y, sec):
        n = int(self.sample_rate * sec)
        k = len(y) // n
        return np.sqrt((y[:k * n].reshape(k, n) ** 2).mean(axis=1)) if k else np.array([])

    def analyze_audio_chunk(self, audio_data, floor=0.01):
        """Accepts 16-bit PCM bytes or a float array. Returns metrics, or None for empty input."""
        try:
            y = (np.frombuffer(audio_data, dtype=np.int16).astype(np.float32) / 32768.0
                 if isinstance(audio_data, (bytes, bytearray)) else np.asarray(audio_data, dtype=np.float32))
            if len(y) == 0:
                return None
            rms = self._frames(y, .25)
            if rms.size == 0:
                rms = np.array([np.sqrt((y ** 2).mean())])
            speech = float((rms > max(floor, 2 * np.percentile(rms, 20))).mean()) if rms.size > 1 else float(rms[0] > floor * 2)
            db = float(20 * np.log10(np.sqrt((y ** 2).mean()) + 1e-9))
            return dict(noise_db=round(db, 1), speech_ratio=round(speech, 3),
                        state="speech" if speech > .3 else ("noise" if db > -35 else "silence"))
        except Exception as e:
            print("Audio error:", e)
            return None

    def analyze_file(self, path, win=30):
        """Per-window metrics aligned with the video timeline. Returns None if no audio track."""
        try:
            import librosa
            y, _ = librosa.load(path, sr=self.sample_rate, mono=True)
        except Exception:
            return None
        if len(y) < self.sample_rate:
            return None
        rms = self._frames(y, .5)
        thr = max(0.01, 2 * np.percentile(rms, 20))
        per = int(win / .5)
        out = []
        for w in range(int(np.ceil(len(rms) / per))):
            seg = rms[w * per:(w + 1) * per]
            out.append(dict(activity=round(float((seg > thr).mean()), 3),
                            noise_db=round(float(20 * np.log10(seg.mean() + 1e-9)), 1)))
        return out
