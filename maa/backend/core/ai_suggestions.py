import os


class AISuggestionEngine:
    """Rule-based suggestions always run (offline). If GROQ_API_KEY is set, an LLM adds a short narrative
    built from aggregate numbers only (no video, no faces leave the machine)."""

    def generate_suggestions(self, data):
        rules = self._rules(data["timeline"], [s for s in data["students"] if s["status"] == "Present"], data["duration"])
        return rules, self._llm(data)

    def _llm(self, d):
        key = os.getenv("GROQ_API_KEY")
        if not key:
            return None
        try:
            from groq import Groq
            prompt = (f"Classroom session {d['duration_label']}, {d['present_count']} present, avg engagement "
                      f"{d['avg_engagement']:.0%}. Engagement per 30s window: {[w['engagement'] for w in d['timeline']]}. "
                      "Give 3 short, practical teaching suggestions.")
            r = Groq(api_key=key).chat.completions.create(
                model=os.getenv("GROQ_MODEL", "llama-3.1-8b-instant"), temperature=.5, max_tokens=250,
                messages=[{"role": "system", "content": "You are an expert AI teaching assistant. You advise; the teacher decides."},
                          {"role": "user", "content": prompt}])
            return r.choices[0].message.content
        except Exception as e:
            print(f"AI Suggestion Error: {e}")
            return None

    def _rules(self, tl, present, dur):
        out = []
        add = lambda p, t, d: out.append(dict(priority=p, title=t, detail=d))
        sc = [w["engagement"] for w in tl if w["people"] > 0]
        if not sc:
            return [dict(priority="high", title="No participants detected",
                         detail="Check camera angle and lighting; faces should be at least ~40 px wide.")]
        avg = sum(sc) / len(sc)
        if avg < .4:
            add("high", "Overall engagement was low", f"Average {avg:.0%}. Open with a question and keep lecture blocks to 10–15 minutes.")
        for k in range(1, len(tl)):
            if tl[k]["people"] and tl[k - 1]["engagement"] - tl[k]["engagement"] >= .2:
                add("medium", f"Attention drop at {tl[k]['label']}", "Try a quick poll, recap question or short break here.")
                break
        best = max(tl, key=lambda w: w["engagement"])
        if best["engagement"] >= .6:
            add("info", f"Engagement peaked at {best['label']}", "Reuse whatever format you used here.")
        au = [w["audio"] for w in tl]
        if au and all(a is not None for a in au):
            run = mx = 0
            for a in au:
                run = run + 1 if a < .1 else 0; mx = max(mx, run)
            if mx >= 3:
                add("medium", "Long stretch with no speech", f"About {mx * 30 // 60} min with almost no interaction. Add a discussion prompt.")
        h = len(sc) // 2
        if h >= 2 and sum(sc[h:]) / (len(sc) - h) < sum(sc[:h]) / h - .1:
            add("medium", "Engagement faded in the second half", "Split the session into shorter segments with a break near the middle.")
        if present:
            late = [s for s in present if s["first_seen_s"] > .2 * dur]
            if late:
                add("info", f"{len(late)} late arrival(s)", "Repeat key announcements briefly after the start.")
            if len([s for s in present if s["attention"] < .5]) >= .3 * len(present):
                add("medium", "Many learners facing away", "Check seating and whether the board/screen is easy to see.")
            still = [s for s in present if s["inactive_seconds"] > .25 * s["present_seconds"]]
            if still:
                add("low", f"{len(still)} learner(s) were still for long periods", "Invite them in with low-pressure questions or pair work.")
        return out or [dict(priority="info", title="Engagement was stable", detail="No major issues found.")]
