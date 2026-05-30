# GrokScribe ER - App Summary

## Core Information
**Name:** GrokScribe ER (working title)  
**Type:** Progressive Web App (PWA) – works in browser and can be installed on iPhone/Android home screen  
**Platform:** Streamlit (Python) hosted on Streamlit Community Cloud  
**Target User:** Emergency Physicians

## Core Purpose
An ambient listening scribe that records patient encounters, transcribes them, and automatically generates structured clinical notes optimized for **ER workflow and 2023 AMA E/M billing guidelines**. The goal is to dramatically reduce documentation time while improving note quality and billing accuracy.

## Current Features
- **Ambient Recording**: One-tap microphone recording of patient encounters
- **Transcription**: Uses OpenAI Whisper API (high accuracy)
- **Structured Note Generation** with these exact sections:
  - History of Present Illness (HPI)
  - Review of Systems (ROS)
  - Physical Examination (PE)
  - Medical Decision Making (MDM)
  - Impression and Plan
- **Additional Data Input**: Large text box to paste labs, imaging, EKG, or full EHR chart from transferring hospitals
- **Individual Copy Buttons**: One-click copy for each section + full chart copy
- **MDM Quality**: Uses user's custom detailed prompt + 2023 AMA E/M Guidelines (focus on Number/Complexity of Problems, Data Reviewed, and Risk)
- **Clean Minimal Design**: Dark mode, mobile-friendly, simple interface

## Tech Stack
- **Frontend**: Streamlit (Python)
- **APIs**: OpenAI (Whisper + GPT-4o) + Grok (xAI)
- **Hosting**: Streamlit Community Cloud (free tier)
- **Deployment**: GitHub → Streamlit Cloud

## Current Status
- Basic version is working (records → transcribes → generates structured note)
- Has had some issues with Grok model names (currently switching to GPT-4o for reliability)
- Needs further refinement on MDM quality and section formatting

## Long-Term Vision
- Add photo interpretation (EKG, radiology reports, lab results from outside hospitals)
- Eventually support wearables (Google Glass/Meta Glass) with audio + visual input
- Full offline capability where possible
- Direct EHR integration (Epic, Cerner, Athena, etc.)
- Scale to other specialties beyond ER

## Key Challenges
- Grok API model name changes causing errors
- Need for reliable MDM generation that follows 2023 E/M guidelines
- Making the app as simple and reliable as possible for a non-coder physician
- HIPAA compliance for production deployment
- Multi-user support and patient record management
