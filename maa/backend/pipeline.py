import cv2, time
from core.face_detection import FaceDetector
from core.tracker import PresenceTracker
from core.camera_service import CameraService
from core.audio_analysis import AudioAnalyzer
from core.multimodal_agent import MultimodalAgent, WIN, mmss
from core.analytics import student_analytics
from core.ai_suggestions import AISuggestionEngine


def process(source, max_seconds=None, sample_fps=4, min_presence=10, progress=lambda p: None):
    live = isinstance(source, int)
    if live:
        cam = CameraService(source); cam.start(); read = cam.get_frame; fps, total = 25, 0
    else:
        cap = cv2.VideoCapture(source)
        if not cap.isOpened():
            raise RuntimeError("Cannot open video file")
        fps, total = cap.get(cv2.CAP_PROP_FPS) or 25, cap.get(cv2.CAP_PROP_FRAME_COUNT)
        read = lambda: cap.read()[1]
    step = max(1, round(fps / sample_fps)); dt = 1 / sample_fps if live else step / fps
    det, trk, agent = FaceDetector(), PresenceTracker(), MultimodalAgent()
    i, t, last, t0 = 0, 0.0, -9.0, time.time()
    try:
        while True:
            frame = read()
            if frame is None:
                break
            i += 1
            if live:
                t = time.time() - t0
                if max_seconds and t > max_seconds: break
                if t - last < dt: continue
                last = t
            else:
                if (i - 1) % step: continue
                t = (i - 1) / fps
            agent.add_vision(t, trk.update(t, dt, det.process_frame(frame)))
            progress(min(t / (max_seconds or 60), .99) if live else min(i / max(total, 1), .99))
    finally:
        cam.stop() if live else cap.release()
    duration = max(t, dt)
    audio = None if live else AudioAnalyzer().analyze_file(source, WIN)
    agent.set_audio(audio)
    tl, students = agent.timeline(duration), student_analytics(trk.tracks, min_presence)
    avg = sum(w["engagement"] for w in tl) / len(tl)
    res = dict(duration=round(duration, 1), duration_label=mmss(duration), has_audio=audio is not None,
               present_count=sum(s["status"] == "Present" for s in students),
               peak_people=max(w["people"] for w in tl), avg_engagement=round(avg, 3), students=students, timeline=tl)
    res["suggestions"], res["ai_summary"] = AISuggestionEngine().generate_suggestions(res)
    return res
