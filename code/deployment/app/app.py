"""A small UI that gets every prediction from the separate API service."""
import os

import requests
import streamlit as st

API_URL = os.getenv("API_URL", "http://localhost:8000")
st.set_page_config(page_title="Hull Lab | Yacht Resistance", page_icon="⛵", layout="centered")
st.markdown("### ⛵ HULL LAB")
st.title("Explore yacht resistance")
st.write("Adjust a hull’s geometry and speed to estimate its residuary resistance per unit displacement weight.")
st.caption("Delft yacht experiments · 308 observations · Extra Trees regression")

with st.form("prediction"):
    left, right = st.columns(2)
    with left:
        buoyancy = st.number_input("Buoyancy position", min_value=-10.0, max_value=10.0, value=-2.3, step=0.1, help="Dimensionless longitudinal center of buoyancy.")
        prismatic = st.number_input("Prismatic coefficient", min_value=0.01, max_value=0.99, value=0.558, step=0.001, format="%.3f")
        length_displacement = st.number_input("Length / displacement ratio", min_value=0.1, max_value=20.0, value=4.78, step=0.01)
    with right:
        beam_draught = st.number_input("Beam / draught ratio", min_value=0.1, max_value=20.0, value=3.99, step=0.01)
        length_beam = st.number_input("Length / beam ratio", min_value=0.1, max_value=20.0, value=3.17, step=0.01)
        froude = st.number_input("Froude number", min_value=0.01, max_value=1.0, value=0.3, step=0.025, format="%.3f", help="Dimensionless speed: velocity / sqrt(gravity × waterline length).")
    submitted = st.form_submit_button("Predict resistance", type="primary", use_container_width=True)

if submitted:
    try:
        with st.spinner("Estimating resistance…"):
            response = requests.post(API_URL + "/predict", json={"buoyancy": buoyancy, "prismatic": prismatic,
                "length_displacement": length_displacement, "beam_draught": beam_draught, "length_beam": length_beam, "froude": froude}, timeout=15)
            response.raise_for_status()
            result = response.json()
        st.metric("Predicted residuary resistance", f"{result['resistance']:.3f}")
        st.caption(result["unit"])
        for warning in result["warnings"]:
            st.warning(warning)
        st.caption("Model run: " + result["mlflow_run_id"])
    except (requests.RequestException, ValueError, KeyError):
        st.error("The prediction service is temporarily unavailable. Please try again shortly.")

with st.expander("About the model and evaluation"):
    st.write("The model uses five hull geometry measurements plus the Froude number and its squared and cubed values. Entire hull designs are held out for testing.")
    st.write("All inputs and predictions use the original dataset’s dimensionless scale. This is an educational model for the sampled hull family.")
    st.markdown("[Dataset and attribution](https://archive.ics.uci.edu/dataset/243/yacht+hydrodynamics)")
