
import streamlit as st
import subprocess
import os

st.set_page_config(page_title="CV Volume Control", layout="centered")

st.title("🖐️ Gesture-Based Volume Control")
st.markdown("This Streamlit interface launches your MediaPipe volume controller app with one click.")

# Set parameters (if any were to be added)
volume_level = st.slider("Initial Volume Level (%)", 0, 100, 50)

# Run the existing script
if st.button("▶️ Start Volume Controller"):
    st.success("Launching the app... A new window will open.")
    # Launch in background
    subprocess.Popen(["python3", "cv-volume.py"])

st.markdown("---")
st.write("ℹ️ Make sure your webcam and audio output are working properly before launching.")
