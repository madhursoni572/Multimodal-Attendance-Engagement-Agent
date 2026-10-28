import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
from fastapi.testclient import TestClient
from main import app
from core.audio_analysis import AudioAnalyzer
import numpy as np

c = TestClient(app)

def test_health(): assert c.get("/health").json() == {"status": "ok"}
def test_site(): assert "Classroom Pulse" in c.get("/").text
def test_unknown_job(): assert c.get("/api/jobs/nope").status_code == 404
def test_audio_silence_vs_tone():
    a = AudioAnalyzer(); n = 16000
    assert a.analyze_audio_chunk(np.zeros(n))["state"] == "silence"
    tone = (np.sin(np.linspace(0, 800, n)) * 0.3).astype(np.float32)
    assert a.analyze_audio_chunk(tone)["noise_db"] > -30
