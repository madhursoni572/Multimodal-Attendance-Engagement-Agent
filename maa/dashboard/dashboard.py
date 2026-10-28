import os, time, requests, pandas as pd, streamlit as st

API = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Attendance & Engagement Agent", layout="wide")
st.title("Attendance & Engagement Agent")
st.caption("Runs on your own server. Faces are not identified and uploaded video is deleted after analysis.")


def run(resp):
    if not resp.ok:
        st.error(resp.text); return
    jid, bar = resp.json()["job"], st.progress(0.0)
    while True:
        j = requests.get(f"{API}/api/jobs/{jid}").json()
        bar.progress(min(float(j.get("progress", 0)), 1.0))
        if j["status"] != "running": break
        time.sleep(1)
    if j["status"] == "error": st.error(j["error"])
    else: st.session_state.update(r=j["result"], jid=jid)


c1, c2 = st.columns(2)
with c1:
    f = st.file_uploader("Classroom recording", type=["mp4", "avi", "mov", "mkv"])
    mp = st.number_input("Minimum presence (seconds)", 2, 300, 10)
    if st.button("Analyse recording", disabled=f is None):
        run(requests.post(f"{API}/api/analyze", files={"video": (f.name, f.getvalue())}, data={"min_presence": mp}))
with c2:
    secs = st.number_input("Webcam duration (seconds)", 10, 3600, 60)
    if st.button("Analyse server webcam"):
        run(requests.post(f"{API}/api/webcam", data={"seconds": secs, "min_presence": mp}))

r = st.session_state.get("r")
if r:
    a, b, c, d = st.columns(4)
    a.metric("Session length", r["duration_label"]); b.metric("Counted present", r["present_count"])
    c.metric("Peak faces in view", r["peak_people"]); d.metric("Average engagement", f"{r['avg_engagement']:.0%}")
    st.subheader("Engagement over time")
    st.line_chart(pd.DataFrame(r["timeline"]).set_index("label")[["engagement", "attention", "audio"]])
    st.subheader("Teaching suggestions")
    for s in r["suggestions"]:
        (st.error if s["priority"] == "high" else st.warning if s["priority"] == "medium" else st.info)(f"**{s['title']}**  \n{s['detail']}")
    if r.get("ai_summary"): st.markdown("**AI summary**\n\n" + r["ai_summary"])
    st.subheader("Student session analytics")
    st.dataframe(pd.DataFrame(r["students"]), use_container_width=True)
    st.download_button("Download CSV", requests.get(f"{API}/api/export/{st.session_state['jid']}.csv").content, "session.csv", "text/csv")
