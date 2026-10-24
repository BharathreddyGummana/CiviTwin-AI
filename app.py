import io
import sqlite3
from datetime import datetime
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from PIL import Image
import cv2
import numpy as np
import folium
from streamlit_folium import st_folium

APP_DIR = Path(__file__).parent
DB_PATH = APP_DIR / "civitwin.db"
SAMPLE_PATH = APP_DIR / "data" / "sample_roads.csv"

st.set_page_config(page_title="CiviTwin AI", page_icon="🌧️", layout="wide")

st.markdown("""
<style>
.main {background-color:#f7fafc;}
.block-container {padding-top:1.4rem;}
.hero {padding:1.1rem 1.4rem;border-radius:16px;background:linear-gradient(120deg,#0f3d56,#167d8d);color:white;}
.small-note {font-size:0.88rem;color:#52616b;}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="hero"><h1>🌧️ CiviTwin AI</h1><h3>AI-Powered Flood Preparedness Planner for Local Roads and Drains</h3><p>Prepare streets for heavy rain before it arrives.</p></div>', unsafe_allow_html=True)
st.caption("Decision-support prototype • Use verified field observations before taking real-world action.")

def init_db():
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""CREATE TABLE IF NOT EXISTS inspections (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            created_at TEXT, segment_id TEXT, road_name TEXT, latitude REAL, longitude REAL,
            rainfall REAL, blockage REAL, damage REAL, vulnerability REAL, importance REAL,
            risk REAL, risk_level TEXT, defects TEXT, notes TEXT, actions TEXT
        )""")
init_db()

def risk_score(w, b, d, v, i):
    # All inputs are normalized to 0-100. Weights are demonstration assumptions from the proposal.
    return round(0.30*w + 0.25*b + 0.20*d + 0.15*v + 0.10*i, 2)

def level(score):
    if score >= 70: return "High"
    if score >= 40: return "Medium"
    return "Low"

def recommendations(w, b, d, v, i, score):
    actions = []
    if b >= 50: actions.append("Clear and inspect drains before forecast rainfall")
    if d >= 50: actions.append("Verify road defects; schedule pothole/crack repair")
    if w >= 60: actions.append("Inspect low spots and prepare temporary water diversion")
    if v >= 60: actions.append("Prioritize nearby schools, hospitals, and low-lying households")
    if i >= 70: actions.append("Coordinate traffic warning and alternate-route planning")
    if score >= 70: actions.insert(0, "URGENT: conduct a field inspection and prepare a local response")
    elif score >= 40: actions.insert(0, "Schedule pre-rain inspection and confirm responsible team")
    if not actions: actions.append("Continue routine inspection and monitor rainfall forecasts")
    return actions

def cv_screen(uploaded):
    """Transparent image screening: OpenCV visual indicators, not a trained defect classifier."""
    image = Image.open(uploaded).convert("RGB")
    arr = np.array(image)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 70, 150)
    edge_ratio = float((edges > 0).mean())
    # Heuristic only: image texture cannot reliably establish a pothole/crack.
    indicator = min(100, round(edge_ratio * 500, 1))
    return image, edge_ratio, indicator, edges

def load_records():
    try:
        df = pd.read_csv(SAMPLE_PATH)
    except Exception:
        df = pd.DataFrame(columns=["segment_id","road_name","latitude","longitude","rainfall","blockage","damage","vulnerability","importance","risk","risk_level","defects","notes","actions"])
    with sqlite3.connect(DB_PATH) as con:
        saved = pd.read_sql_query("SELECT * FROM inspections ORDER BY id DESC", con)
    if not saved.empty:
        saved["segment_id"] = saved["segment_id"].astype(str)
        df = pd.concat([df, saved], ignore_index=True, sort=False)
    return df

pages = ["Overview Dashboard", "Road Inspection", "Risk Assessment", "Flood Risk Map", "Preparedness Plan & Reports", "About & References"]
page = st.sidebar.radio("Navigate", pages)
st.sidebar.info("Risk score = 0.30W + 0.25B + 0.20D + 0.15V + 0.10I")
st.sidebar.caption("Illustrative weights only; calibrate and validate with field data.")

if page == "Overview Dashboard":
    st.subheader("Flood preparedness at a glance")
    df = load_records()
    if df.empty:
        st.info("No records yet. Use **Road Inspection** or **Risk Assessment** to add a segment.")
    else:
        # Ensure computed values exist for older/sample rows
        if "risk" not in df or df["risk"].isna().all():
            df["risk"] = df.apply(lambda r: risk_score(r.rainfall, r.blockage, r.damage, r.vulnerability, r.importance), axis=1)
        df["risk_level"] = df["risk"].apply(level)
        c1,c2,c3,c4 = st.columns(4)
        c1.metric("Road segments", len(df))
        c2.metric("High risk", int((df["risk_level"]=="High").sum()))
        c3.metric("Medium risk", int((df["risk_level"]=="Medium").sum()))
        c4.metric("Average score", f"{df['risk'].mean():.1f}/100")
        left,right = st.columns(2)
        with left:
            fig = px.bar(df.sort_values("risk", ascending=False), x="segment_id", y="risk", color="risk_level",
                         title="Risk score by road segment", hover_data=["road_name"])
            st.plotly_chart(fig, use_container_width=True)
        with right:
            counts = df["risk_level"].value_counts().rename_axis("Risk level").reset_index(name="Segments")
            st.plotly_chart(px.pie(counts, names="Risk level", values="Segments", title="Risk category distribution"), use_container_width=True)
        st.markdown("#### Ranked readiness table")
        cols = [c for c in ["segment_id","road_name","risk","risk_level","rainfall","blockage","damage","vulnerability","importance","actions"] if c in df.columns]
        st.dataframe(df.sort_values("risk", ascending=False)[cols], use_container_width=True, hide_index=True)

elif page == "Road Inspection":
    st.subheader("1. Road inspection and image screening")
    st.write("Upload a road photograph. The prototype shows OpenCV edge/texture indicators for review; this is **not a trained pothole/crack detector**.")
    uploaded = st.file_uploader("Upload road photograph", type=["png","jpg","jpeg"])
    if uploaded:
        image, edge_ratio, indicator, edges = cv_screen(uploaded)
        c1,c2 = st.columns(2)
        with c1:
            st.image(image, caption="Uploaded road photograph", use_container_width=True)
        with c2:
            st.image(edges, caption="OpenCV Canny edge map", use_container_width=True, clamp=True)
        st.metric("Edge-density indicator (heuristic)", f"{indicator}/100")
        st.caption("This indicator only measures image edges. A human inspector must confirm whether defects are present.")
        confirmed = st.selectbox("Human verification status", ["Not reviewed", "Defect verified", "No defect verified"])
        defect_notes = st.text_area("Verified defects / inspection notes", placeholder="Example: two potholes near the road shoulder; drain cover partly blocked")
        st.session_state["inspection_photo_name"] = uploaded.name
        st.session_state["inspection_confirmed"] = confirmed
        st.session_state["inspection_notes"] = defect_notes
    st.markdown("#### Segment details")
    with st.form("inspection_form"):
        a,b = st.columns(2)
        segment = a.text_input("Segment ID", value=f"SEG-{datetime.now().strftime('%H%M%S')}")
        road = b.text_input("Road name / locality", value="Sample Road")
        c,d = st.columns(2)
        lat = c.number_input("Latitude", value=14.4673, format="%.6f")
        lon = d.number_input("Longitude", value=78.8242, format="%.6f")
        notes = st.text_area("Additional notes")
        submitted = st.form_submit_button("Save inspection record")
    if submitted:
        st.session_state["last_segment"] = {"segment_id":segment,"road_name":road,"latitude":lat,"longitude":lon,
            "notes":notes + " " + st.session_state.get("inspection_notes",""),
            "defects":st.session_state.get("inspection_confirmed","Not reviewed")}
        st.success("Inspection details captured in this session. Use Risk Assessment to score and save the segment.")

elif page == "Risk Assessment":
    st.subheader("2. Risk assessment and explainable score")
    st.write("Enter values from 0 to 100. Rainfall is represented as a normalized waterlogging-risk input, not millimetres.")
    saved = st.session_state.get("last_segment", {})
    with st.form("risk_form"):
        c1,c2,c3 = st.columns(3)
        w = c1.slider("W — Waterlogging risk",0,100,55)
        b = c2.slider("B — Drain blockage severity",0,100,45)
        d = c3.slider("D — Road damage severity",0,100,35)
        c4,c5 = st.columns(2)
        v = c4.slider("V — Vulnerability (low-lying / critical sites)",0,100,40)
        i = c5.slider("I — Road importance",0,100,60)
        st.markdown("**Segment details**")
        seg = st.text_input("Segment ID", value=saved.get("segment_id","SEG-001"))
        road = st.text_input("Road name", value=saved.get("road_name","Sample Road"))
        lat = st.number_input("Latitude", value=float(saved.get("latitude",14.4673)), format="%.6f")
        lon = st.number_input("Longitude", value=float(saved.get("longitude",78.8242)), format="%.6f")
        defect = st.text_input("Verified defect status", value=saved.get("defects","Not reviewed"))
        notes = st.text_area("Notes", value=saved.get("notes",""))
        go = st.form_submit_button("Calculate risk and save")
    if go:
        score = risk_score(w,b,d,v,i)
        risklevel = level(score)
        actions = recommendations(w,b,d,v,i,score)
        st.session_state["last_result"] = {"segment_id":seg,"road_name":road,"latitude":lat,"longitude":lon,"W":w,"B":b,"D":d,"V":v,"I":i,"risk":score,"risk_level":risklevel,"actions":actions}
        with sqlite3.connect(DB_PATH) as con:
            con.execute("""INSERT INTO inspections
                (created_at,segment_id,road_name,latitude,longitude,rainfall,blockage,damage,vulnerability,importance,risk,risk_level,defects,notes,actions)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
                (datetime.now().isoformat(timespec="seconds"),seg,road,lat,lon,w,b,d,v,i,score,risklevel,defect,notes,"; ".join(actions)))
        st.success("Risk score saved to the local SQLite database.")
    result = st.session_state.get("last_result")
    if result:
        st.metric("Road-segment priority score", f"{result['risk']}/100", result["risk_level"] + " risk")
        st.progress(int(result["risk"]))
        st.markdown("#### Why this score?")
        parts = [
            ("Waterlogging", result["W"], .30), ("Drain blockage", result["B"], .25),
            ("Road damage", result["D"], .20), ("Vulnerability", result["V"], .15),
            ("Road importance", result["I"], .10)]
        detail = pd.DataFrame([{"Factor":n,"Input (0–100)":x,"Weight":wt,"Contribution":round(x*wt,2)} for n,x,wt in parts])
        st.dataframe(detail, use_container_width=True, hide_index=True)
        st.write(f"**Formula:** {result['risk']} = 0.30×{result['W']} + 0.25×{result['B']} + 0.20×{result['D']} + 0.15×{result['V']} + 0.10×{result['I']}")
        st.markdown("#### Recommended preparedness actions")
        for action in result["actions"]: st.write("☑️ " + action)

elif page == "Flood Risk Map":
    st.subheader("3. GIS-style flood-risk map")
    df = load_records()
    if df.empty:
        st.info("Add or load segment data to display the map.")
    else:
        if "risk" not in df or df["risk"].isna().all():
            df["risk"] = df.apply(lambda r: risk_score(r.rainfall, r.blockage, r.damage, r.vulnerability, r.importance), axis=1)
        df = df.dropna(subset=["latitude","longitude"])
        if df.empty:
            st.warning("No valid coordinates available.")
        else:
            center = [float(df["latitude"].mean()), float(df["longitude"].mean())]
            m = folium.Map(location=center, zoom_start=13, control_scale=True)
            for _,r in df.iterrows():
                risk = float(r["risk"])
                color = "red" if risk >= 70 else ("orange" if risk >= 40 else "green")
                popup = f"<b>{r.get('segment_id','')}</b><br>{r.get('road_name','')}<br>Score: {risk:.1f}/100<br>Risk: {level(risk)}"
                folium.CircleMarker([float(r["latitude"]),float(r["longitude"])], radius=8, color=color,
                    fill=True, fill_opacity=.8, popup=folium.Popup(popup,max_width=300)).add_to(m)
            st_folium(m, use_container_width=True, height=520)
            st.caption("Map markers are based on entered/sample coordinates. Confirm coordinates and conditions in the field.")

elif page == "Preparedness Plan & Reports":
    st.subheader("4. Prioritized preparedness plan and export")
    df = load_records()
    if df.empty:
        st.info("No road segments found. Add a risk assessment first.")
    else:
        if "risk" not in df or df["risk"].isna().all():
            df["risk"] = df.apply(lambda r: risk_score(r.rainfall, r.blockage, r.damage, r.vulnerability, r.importance), axis=1)
        df["risk_level"] = df["risk"].apply(level)
        if "actions" not in df: df["actions"] = ""
        def fill_actions(row):
            if pd.notna(row.get("actions")) and str(row.get("actions")).strip(): return row["actions"]
            return "; ".join(recommendations(float(row["rainfall"]),float(row["blockage"]),float(row["damage"]),float(row["vulnerability"]),float(row["importance"]),float(row["risk"])))
        df["actions"] = df.apply(fill_actions,axis=1)
        df = df.sort_values("risk", ascending=False)
        st.dataframe(df[[c for c in ["segment_id","road_name","risk","risk_level","actions"] if c in df.columns]],use_container_width=True,hide_index=True)
        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download full preparedness report (CSV)", csv, file_name="civitwin_preparedness_report.csv", mime="text/csv")
        st.download_button("⬇️ Download ranked action plan (CSV)", df[[c for c in ["segment_id","road_name","risk","risk_level","actions"] if c in df.columns]].to_csv(index=False).encode("utf-8"),
                           file_name="civitwin_action_plan.csv", mime="text/csv")
        st.caption("CSV exports contain screening scores and suggested actions, not certified engineering advice.")

else:
    st.subheader("About CiviTwin AI")
    st.write("CiviTwin AI combines road-photo screening, rainfall/waterlogging risk, drainage condition, road damage, vulnerability and road importance into one explainable preparedness workflow.")
    st.markdown("#### Included modules")
    st.markdown("""
    - Road photograph upload and OpenCV edge-map screening
    - Human verification field for detected/observed defects
    - Rainfall, drainage blockage, road damage, vulnerability and road importance inputs
    - Weighted, explainable segment risk score
    - GIS-style interactive map with risk-coloured markers
    - Plotly dashboard, ranked road-segment table and action recommendations
    - CSV downloads for records and prioritized preparedness actions
    - SQLite storage for saved assessments
    """)
    st.markdown("#### Technology stack")
    st.write("Python • Streamlit • OpenCV • Plotly • Folium • pandas • SQLite")
    st.markdown("#### References")
    st.markdown("""
    - RDD2022 Road Damage Detection dataset: https://github.com/sekilab/RoadDamageDetector
    - NASA Global Precipitation Measurement (GPM): https://gpm.nasa.gov/data/directory
    - Streamlit documentation: https://docs.streamlit.io/
    - OpenCV documentation: https://docs.opencv.org/
    - Folium documentation: https://python-visualization.github.io/folium/
    """)
    st.warning("Limitations: the included OpenCV step is a visual heuristic, not a trained defect model. Replace it with a validated model and verified datasets for real deployment. Risk weights are illustrative assumptions and require local field calibration.")
