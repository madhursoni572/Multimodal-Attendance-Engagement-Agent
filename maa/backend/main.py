import os, io, csv, json, uuid, tempfile, threading
from dotenv import load_dotenv
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pipeline import process
from core.audio_analysis import AudioAnalyzer

load_dotenv()
app = FastAPI(title="Multimodal Attendance & Engagement Agent")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("CORS_ORIGINS", "*").split(","),
                   allow_methods=["*"], allow_headers=["*"])
DATA = os.getenv("DATA_DIR", "data"); os.makedirs(DATA, exist_ok=True)
JOBS = {}


def _run(jid, src, **kw):
    job = JOBS[jid]
    try:
        job["result"] = process(src, progress=lambda p: job.__setitem__("progress", round(p, 3)), **kw)
        job["status"], job["progress"] = "done", 1
        json.dump(job["result"], open(os.path.join(DATA, jid + ".json"), "w"))
    except Exception as e:
        job["status"], job["error"] = "error", str(e)
    finally:
        if isinstance(src, str) and os.path.exists(src):
            os.remove(src)  # privacy: raw video deleted after analysis


def _start(src, **kw):
    jid = uuid.uuid4().hex[:12]
    JOBS[jid] = dict(status="running", progress=0)
    threading.Thread(target=_run, args=(jid, src), kwargs=kw, daemon=True).start()
    return {"job": jid}


def _job(jid):
    if jid in JOBS: return JOBS[jid]
    p = os.path.join(DATA, jid + ".json")
    if os.path.exists(p): return dict(status="done", progress=1, result=json.load(open(p)))
    raise HTTPException(404, "Unknown job")


@app.get("/health")
def health(): return {"status": "ok"}


@app.post("/api/analyze")
async def analyze(video: UploadFile = File(...), min_presence: float = Form(10)):
    fd, path = tempfile.mkstemp(suffix=os.path.splitext(video.filename or ".mp4")[1], dir=DATA)
    with os.fdopen(fd, "wb") as f:
        while chunk := await video.read(1 << 20):
            f.write(chunk)
    return _start(path, min_presence=min_presence)


@app.post("/api/webcam")
def webcam(camera: int = Form(0), seconds: float = Form(60), min_presence: float = Form(10)):
    return _start(camera, max_seconds=seconds, min_presence=min_presence)


@app.get("/api/jobs/{jid}")
def job(jid: str): return _job(jid)


@app.get("/api/export/{jid}.csv")
def export(jid: str):
    j = _job(jid)
    if j["status"] != "done": raise HTTPException(409, "Not ready")
    r, buf = j["result"], io.StringIO(); w = csv.writer(buf)
    w.writerow(["participant", "status", "first_seen", "last_seen", "present_seconds", "attention", "inactive_seconds", "engagement", "intervals"])
    for s in r["students"]:
        w.writerow([s[k] for k in ("id", "status", "first_seen", "last_seen", "present_seconds", "attention", "inactive_seconds", "engagement", "intervals")])
    w.writerow([]); w.writerow(["window", "people", "attention", "motion", "audio", "noise_db", "engagement", "level"])
    for t in r["timeline"]:
        w.writerow([t[k] for k in ("label", "people", "attention", "motion", "audio", "noise_db", "engagement", "level")])
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename=session_{jid}.csv"})


@app.websocket("/ws/audio")
async def ws_audio(ws: WebSocket):
    """Browser mic stream (16-bit PCM bytes, 16 kHz) -> live noise/speech metrics."""
    await ws.accept(); an = AudioAnalyzer()
    try:
        while True:
            m = an.analyze_audio_chunk(await ws.receive_bytes())
            if m: await ws.send_json(m)
    except WebSocketDisconnect:
        pass


# Serve the website from the same service (must stay last so API routes win).
from fastapi.staticfiles import StaticFiles
app.mount("/", StaticFiles(directory=os.path.join(os.path.dirname(os.path.abspath(__file__)), "static"), html=True), name="site")
