"""Multimodal fusion + transparent rule-based engagement scoring (edit the constants to tune)."""
WIN = 30
W_AV = dict(att=.45, mot=.2, aud=.2, act=.15)   # with audio
W_V = dict(att=.55, mot=.25, act=.2)            # video only
LEVELS = [(.65, "High"), (.4, "Medium"), (0, "Low")]
MOTION_FULL = .12                               # movement (face widths) that counts as fully active


def mmss(s):
    s = int(s)
    return f"{s // 60:02d}:{s % 60:02d}"


class MultimodalAgent:
    def __init__(self):
        self.w, self.audio = {}, None

    def add_vision(self, t, obs):
        W = self.w.setdefault(int(t // WIN), dict(s=0, ppl=0, front=0, obs=0, move=0.0, idle=0))
        W["s"] += 1; W["ppl"] += len(obs)
        for o in obs:
            W["front"] += o["frontal"]; W["obs"] += 1; W["move"] += o["move"]; W["idle"] += o["inactive"]

    def set_audio(self, windows):
        self.audio = windows

    def timeline(self, duration):
        out = []
        for k in range(int(duration // WIN) + 1):
            W, a = self.w.get(k), (self.audio[k] if self.audio and k < len(self.audio) else None)
            row = dict(label=mmss(k * WIN), start=k * WIN, people=0, attention=0, motion=0, idle=0, engagement=0,
                       level="Low", audio=a["activity"] if a else None, noise_db=a["noise_db"] if a else None)
            if W and W["obs"]:
                att, mot, idl = W["front"] / W["obs"], min(W["move"] / W["obs"] / MOTION_FULL, 1), W["idle"] / W["obs"]
                s = (W_AV["att"] * att + W_AV["mot"] * mot + W_AV["aud"] * a["activity"] + W_AV["act"] * (1 - idl)
                     if a else W_V["att"] * att + W_V["mot"] * mot + W_V["act"] * (1 - idl))
                row.update(people=round(W["ppl"] / W["s"], 1), attention=round(att, 3), motion=round(mot, 3),
                           idle=round(idl, 3), engagement=round(s, 3),
                           level=next(n for th, n in LEVELS if s >= th))
            out.append(row)
        return out
