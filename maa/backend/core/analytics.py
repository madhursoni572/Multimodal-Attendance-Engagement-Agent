from .multimodal_agent import mmss, MOTION_FULL


def student_analytics(tracks, min_presence=10):
    """Presence-based attendance: seen >= min_presence AND one continuous streak >= half of it."""
    out = []
    for tid, tr in tracks.items():
        if tr["seen"] < 2:
            continue
        ok = tr["seen"] >= min_presence and tr["best"] >= min_presence / 2
        att, mot = tr["att"] / tr["n"], min(tr["move"] / tr["n"] / MOTION_FULL, 1)
        eng = .6 * att + .2 * mot + .2 * (1 - min(tr["inactive"] / tr["seen"], 1))
        iv = ", ".join(f"{mmss(a)}-{mmss(b)}" for a, b in tr["segs"])
        out.append(dict(intervals=iv, id=f"P{tid}", status="Present" if ok else "Not counted (brief)",
                        first_seen=mmss(tr["first"]), last_seen=mmss(tr["last"]), first_seen_s=round(tr["first"], 1),
                        present_seconds=round(tr["seen"], 1), longest_streak=round(tr["best"], 1),
                        attention=round(att, 3), inactive_seconds=round(tr["inactive"], 1), engagement=round(eng, 3)))
    return out
