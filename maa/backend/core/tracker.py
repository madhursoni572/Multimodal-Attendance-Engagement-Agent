import numpy as np


class PresenceTracker:
    """Centroid tracker that also accumulates presence duration, stillness and attention per participant."""

    def __init__(self, expire=10, idle_move=0.03, idle_s=15):
        self.tracks, self.nid = {}, 1
        self.expire, self.idle_move, self.idle_s = expire, idle_move, idle_s

    def update(self, t, dt, dets):
        cen = [(d["bbox"][0] + d["bbox"][2] / 2, d["bbox"][1] + d["bbox"][3] / 2, d["bbox"][2]) for d in dets]
        pairs = sorted((float(np.hypot(tr["c"][0] - c[0], tr["c"][1] - c[1])), tid, i)
                       for tid, tr in self.tracks.items() if t - tr["last"] < self.expire
                       for i, c in enumerate(cen))
        ut, ui, assign = set(), set(), {}
        for d, tid, i in pairs:
            if tid not in ut and i not in ui and d < 1.2 * cen[i][2]:
                assign[i] = tid; ut.add(tid); ui.add(i)
        out = []
        for i, d in enumerate(dets):
            if i not in assign:
                self.tracks[self.nid] = dict(first=t, last=t, c=None, seen=0.0, streak=0.0, best=0.0, att=0,
                                             n=0, move=0.0, idle=0.0, inactive=0.0, segs=[])
                assign[i] = self.nid; self.nid += 1
            tr, (cx, cy, w) = self.tracks[assign[i]], cen[i]
            mv = 0.0 if tr["c"] is None else min(float(np.hypot(cx - tr["c"][0], cy - tr["c"][1])) / w, .5)
            tr["streak"] = tr["streak"] + dt if tr["n"] and (t - tr["last"]) <= 3 * dt else dt
            if tr["n"] and t - tr["last"] <= 5: tr["segs"][-1][1] = t
            else: tr["segs"].append([t, t])
            tr["best"] = max(tr["best"], tr["streak"])
            tr["seen"] += dt; tr["last"] = t; tr["c"] = (cx, cy); tr["n"] += 1
            tr["att"] += int(d["frontal"]); tr["move"] += mv
            tr["idle"] = tr["idle"] + dt if mv < self.idle_move else 0.0
            inactive = tr["idle"] >= self.idle_s
            tr["inactive"] += dt if inactive else 0
            out.append(dict(id=assign[i], frontal=int(d["frontal"]), move=mv, inactive=int(inactive)))
        return out
