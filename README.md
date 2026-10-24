# CiviTwin AI — Flood Preparedness Planner

A runnable prototype based on the uploaded CiviTwin AI presentation. It connects road inspection, rainfall/waterlogging risk, drainage blockage, road damage, vulnerability, road importance, GIS-style visualization, prioritized action planning, and CSV reports.
## Live Demo

[Launch CiviTwin AI](https://civitwin-ai-sbdpptscwpbyc4esth5myt.streamlit.app/)

## Features implemented
1. Road photograph upload.
2. OpenCV edge-map / image-texture screening indicator.
3. Human verification and inspection notes.
4. Segment details and coordinates.
5. Inputs normalized to 0–100: W, B, D, V, I.
6. Weighted explainable risk formula: `R = 0.30W + 0.25B + 0.20D + 0.15V + 0.10I`.
7. Low / Medium / High risk classification.
8. Action recommendations based on risk factors.
9. Plotly dashboard and ranked readiness table.
10. Folium interactive map with colored markers.
11. SQLite local persistence.
12. Downloadable full report and action-plan CSV.
13. Limitations, calibration warning, and source references.

## Important honesty note
The included OpenCV operation is **not a trained pothole/crack detector**. It generates an edge-density indicator that can help demonstrate image-processing flow, but it cannot reliably classify road defects. A human must verify the image. For a research-grade version, integrate a trained model and cite its dataset/model, then evaluate it on held-out local road images. The risk weights are demo assumptions from the presentation and are not certified engineering values.

## Setup (Windows)
1. Install Python 3.10 or newer.
2. Extract this ZIP.
3. Open the extracted folder in VS Code.
4. Open Terminal and run:

```powershell
python -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
streamlit run app.py
```

If PowerShell blocks activation, use Command Prompt:
```bat
.venv\\Scripts\\activate.bat
```
Or run the venv Python directly:
```powershell
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe -m streamlit run app.py
```

## Demo flow (about 2 minutes)
1. Open Road Inspection and upload a road image.
2. Record the segment ID, road name and coordinates; save inspection details.
3. Open Risk Assessment, set the five inputs and click Calculate risk and save.
4. Open Overview Dashboard to show the score, category and ranked table.
5. Open Flood Risk Map to show map markers.
6. Open Preparedness Plan & Reports and download the CSV.

## Risk formula
- W = waterlogging risk
- B = drainage blockage severity
- D = road damage severity
- V = vulnerability (low-lying zones / critical sites)
- I = road importance

Every factor must be entered from 0 to 100. Rainfall is represented as a normalized waterlogging-risk score in this prototype; it is not raw rainfall in millimetres.

## Data
`data/sample_roads.csv` includes illustrative sample rows and coordinates for demonstration only. Replace with verified local data before using this for decisions.

## References from the presentation
- RDD2022: https://github.com/sekilab/RoadDamageDetector
- NASA GPM precipitation data: https://gpm.nasa.gov/data/directory
- Streamlit: https://docs.streamlit.io/
- OpenCV: https://docs.opencv.org/
- Folium: https://python-visualization.github.io/folium/
