"""Accuracy + performance check for the README table.
Usage: python tests/evaluate.py clip.mp4 --truth 4 [--min-presence 10]
--truth = number of people who were really present (not counting brief walk-throughs)."""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
import cv2
from pipeline import process

ap = argparse.ArgumentParser()
ap.add_argument("video"); ap.add_argument("--truth", type=int, required=True)
ap.add_argument("--min-presence", type=float, default=10)
a = ap.parse_args()
cap = cv2.VideoCapture(a.video)
dur = cap.get(cv2.CAP_PROP_FRAME_COUNT) / (cap.get(cv2.CAP_PROP_FPS) or 25); cap.release()
t0 = time.time(); r = process(a.video, min_presence=a.min_presence); el = time.time() - t0
found = r["present_count"]
row = (f"| {os.path.basename(a.video)} | {dur:.0f}s | {a.truth} | {found} | {found - a.truth:+d} | "
       f"{el:.1f}s | {dur / max(el, .01):.1f}x | {r['avg_engagement']:.0%} |")
hdr = "| clip | length | actual present | system present | error | processing | speed vs realtime | avg engagement |\n|---|---|---|---|---|---|---|---|"
print(hdr); print(row)
p = os.path.join(os.path.dirname(__file__), "results.md")
new = not os.path.exists(p)
with open(p, "a") as f: f.write((hdr + "\n" if new else "") + row + "\n")
print("\nAppended to tests/results.md. Paste the table into README.md")
