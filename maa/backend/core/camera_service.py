import cv2


class CameraService:
    def __init__(self, camera_id=0):
        self.camera_id, self.cap, self.is_running = camera_id, None, False

    def start(self):
        if self.cap is None:
            self.cap = cv2.VideoCapture(self.camera_id)
            self.is_running = self.cap.isOpened()
            if not self.is_running:
                raise RuntimeError(f"Cannot open camera {self.camera_id}")

    def stop(self):
        if self.cap:
            self.cap.release()
        self.cap, self.is_running = None, False

    def get_frame(self):
        if self.is_running and self.cap:
            ok, frame = self.cap.read()
            if ok:
                return frame
        return None
