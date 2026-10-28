import cv2
print("OpenCV version:", getattr(cv2, "__version__", "unknown"))
print("OpenCV loaded from:", getattr(cv2, "__file__", "unknown"))
print("Has CascadeClassifier:", hasattr(cv2, "CascadeClassifier"))

class FaceDetector:
    """Haar-cascade detector (bundled with OpenCV). Adds a 'frontal' flag: profile faces = looking away."""

    def __init__(self):
        self.front = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
        self.prof = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_profileface.xml")
        if self.front.empty() or self.prof.empty():
            print("Error: Could not load face cascade xml")

    def process_frame(self, frame):
        h, w = frame.shape[:2]
        if w > 640:
            frame = cv2.resize(frame, None, fx=640 / w, fy=640 / w)
        gray = cv2.equalizeHist(cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY))
        dets = [{"bbox": (int(x), int(y), int(a), int(b)), "score": 1.0, "frontal": True}
                for x, y, a, b in self.front.detectMultiScale(gray, 1.1, 5, minSize=(40, 40))]
        for x, y, a, b in self.prof.detectMultiScale(gray, 1.1, 5, minSize=(40, 40)):
            cx, cy = x + a / 2, y + b / 2
            if not any(abs(cx - (p + r / 2)) < r * .6 and abs(cy - (q + s / 2)) < s * .6
                       for p, q, r, s in (d["bbox"] for d in dets)):
                dets.append({"bbox": (int(x), int(y), int(a), int(b)), "score": 1.0, "frontal": False})
        return dets
