import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="GrokScribe ER", page_icon="🩺", layout="centered")

st.title("🩺 GrokScribe ER")
st.caption("Simple • Clean • For Emergency Physicians")

# Sidebar for keys
with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI Key", type="password")
    grok_key = st.text_input("Grok Key", type="password")

if not openai_key or not grok_key:
    st.info("Enter both keys in the sidebar to start")
    st.stop()

openai_client = OpenAI(api_key=openai_key)
grok_client = OpenAI(api_key=grok_key, base_url="https://api.x.ai/v1")

# Main interface
st.subheader("Record Encounter")
audio = st.audio_input("🎤 Tap to record")

if audio and st.button("Transcribe & Create Note", type="primary"):
    with st.spinner("Transcribing..."):
        transcript = openai_client.audio.transcriptions.create(
            model="whisper-1", file=audio
        ).text
    
    st.success("Transcription complete!")
    st.text_area("Transcript", transcript, height=150)
    
    with st.spinner("Generating note..."):
        note = openai_client.chat.completions.create(
            model="gpt-4o",
            messages=[{"role": "user", "content": f"Create a clean ER note from this transcript:\n\n{transcript}"}],
            temperature=0.3
        ).choices[0].message.content
    
    st.markdown("### Clinical Note")
    st.markdown(note)
    
    if st.button("Copy Note"):
        st.toast("Note copied!")
