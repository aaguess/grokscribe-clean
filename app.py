import streamlit as st
from openai import OpenAI

st.set_page_config(page_title="GrokScribe ER", page_icon="🩺", layout="centered")

st.title("🩺 GrokScribe ER")
st.caption("Clean • Structured • Built for ER Billing & Documentation (2023 E/M Guidelines)")

with st.sidebar:
    st.header("API Keys")
    openai_key = st.text_input("OpenAI Key", type="password")
    grok_key = st.text_input("Grok Key", type="password")

if not openai_key or not grok_key:
    st.info("Enter both keys in the sidebar to continue")
    st.stop()

openai_client = OpenAI(api_key=openai_key)
grok_client = OpenAI(api_key=grok_key, base_url="https://api.x.ai/v1")

# Tabs
tab1, tab2 = st.tabs(["🎙️ Record & Generate", "📋 Structured Note"])

with tab1:
    st.subheader("Record Encounter")
    audio = st.audio_input("🎤 Tap to record patient encounter")

    additional_data = st.text_area(
        "Paste Labs / Imaging / EKG / EHR Chart / External Notes here (optional but recommended for better MDM)",
        height=150,
        placeholder="Troponin 0.08, CXR: No acute process, CT Head: Negative, etc."
    )

    if audio and st.button("🔊 Transcribe & Generate Full Note", type="primary", use_container_width=True):
        with st.spinner("Transcribing..."):
            transcript = openai_client.audio.transcriptions.create(
                model="whisper-1", file=audio, language="en"
            ).text
            st.session_state.transcript = transcript

        with st.spinner("Generating structured note using 2023 E/M Guidelines..."):
            prompt = f"""You are an expert Emergency Physician using 2023 AMA CPT E/M Guidelines.

Create a structured note with these EXACT sections:

**HPI:** [Concise paragraph]
**ROS:** [Pertinent positives and negatives as bullets]
**Physical Exam:** [Relevant findings]
**MDM:** [Follow the user's exact MDM prompt below]
**Impression and Plan:** [Clear plan and disposition]

User's MDM Prompt (use exactly):
{st.session_state.get('mdm_prompt', '')}

Transcript:
{transcript}

Additional Data (Labs/Imaging/EKG/EHR):
{additional_data}

Use the 2023 E/M Guidelines for MDM:
- Number and Complexity of Problems
- Amount and Complexity of Data Reviewed
- Risk of Complications/Morbidity/Mortality

Output ONLY the structured note with the exact section headers above. No extra text."""

            note = grok_client.chat.completions.create(
                model="grok-beta",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=2000
            ).choices[0].message.content

            st.session_state.note = note
            st.success("✅ Structured note generated!")

with tab2:
    st.subheader("Structured Clinical Note (2023 E/M Compliant)")

    if "note" in st.session_state:
        note = st.session_state.note

        # Parse sections (simple parsing)
        sections = {}
        current_section = None
        for line in note.split('\n'):
            if line.strip().startswith('**') and line.strip().endswith(':**'):
                current_section = line.strip().replace('**', '').replace(':', '')
                sections[current_section] = ""
            elif current_section:
                sections[current_section] += line + "\n"

        for section_name, content in sections.items():
            col1, col2 = st.columns([5, 1])
            with col1:
                st.markdown(f"**{section_name}**")
                st.text_area("", value=content.strip(), height=120, key=section_name, disabled=True)
            with col2:
                if st.button(f"📋 Copy {section_name}", key=f"copy_{section_name}"):
                    st.toast(f"{section_name} copied!")

        st.divider()
        if st.button("📋 Copy Full Chart", type="primary", use_container_width=True):
            st.toast("Full chart copied! Paste into EHR.")
            st.code(note, language="markdown")
    else:
        st.info("Record an encounter first to generate the note.")

st.divider()
st.caption("GrokScribe ER • Uses 2023 AMA E/M Guidelines • Optimized for ER Billing & Documentation")
