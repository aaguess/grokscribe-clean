# Adelyn ER - Complete Feature Specification

## Name Change: GrokScribe → Adelyn ✨

**Adelyn** = Your daughter's name + your vision: **An AI assistant that lets you practice medicine, not documentation.**

---

## Mission Statement

**Adelyn's purpose:** Free emergency physicians from documentation burden so they can focus on patient care.

**Not:** Feature-rich, complex, full of options
**Yes:** Clean, simple, fewest clicks possible, intuitive

---

## Core Features (MVP Phase)

### 1. Real-Time Translation & Ambient Listening

#### Problem Your Solution Solves:
- Provider speaking English ↔ Patient speaking Spanish/Mandarin/etc.
- Need transcript AND chart elements extracted simultaneously
- Current apps: No real-time translation; post-encounter processing only

#### Adelyn Solution:

**Frontend (React):**
```typescript
// frontend/components/AmbientListener.tsx

import { useRef, useState, useEffect } from 'react';
import { useTranslation } from 'react-i18next'; // Real-time translation

interface AmbientListenerProps {
  patientLanguage: string; // 'en', 'es', 'zh', 'fr', etc.
  onTranscriptUpdate: (transcript: TranscriptSegment[]) => void;
}

export const AmbientListener = ({ 
  patientLanguage, 
  onTranscriptUpdate 
}: AmbientListenerProps) => {
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [isRecording, setIsRecording] = useState(false);
  const [transcript, setTranscript] = useState<TranscriptSegment[]>([]);
  
  // Real-time transcription segments
  interface TranscriptSegment {
    speaker: 'provider' | 'patient';
    language: string;
    originalText: string;
    translatedText?: string;
    timestamp: number;
  }

  const startRecording = async () => {
    const stream = await navigator.mediaDevices.getUserMedia({ 
      audio: { echoCancellation: true, noiseSuppression: true } 
    });
    
    mediaRecorderRef.current = new MediaRecorder(stream);
    setIsRecording(true);
    
    const chunks: BlobPart[] = [];
    mediaRecorderRef.current.ondataavailable = (e) => chunks.push(e.data);
    
    // Stream audio to backend for real-time processing
    const socket = new WebSocket('ws://localhost:8000/ws/transcribe');
    
    socket.onopen = () => {
      mediaRecorderRef.current!.ondataavailable = (e) => {
        socket.send(e.data); // Send audio chunks real-time
      };
    };
    
    socket.onmessage = async (event) => {
      const segment = JSON.parse(event.data);
      // segment = { speaker, originalText, language, timestamp }
      
      // Real-time translation if not English
      if (segment.language !== 'en') {
        segment.translatedText = await translateText(
          segment.originalText,
          segment.language,
          'en'
        );
      }
      
      setTranscript(prev => [...prev, segment]);
      onTranscriptUpdate([...transcript, segment]);
    };

    mediaRecorderRef.current.start(500); // Send chunks every 500ms
  };

  const stopRecording = () => {
    mediaRecorderRef.current?.stop();
    setIsRecording(false);
  };

  return (
    <div className="ambient-listener">
      <div className="header">
        <button 
          onClick={isRecording ? stopRecording : startRecording}
          className={`record-btn ${isRecording ? 'recording' : ''}`}
        >
          {isRecording ? '⏹️ Stop' : '🎤 Start Ambient Listen'}
        </button>
        
        <select value={patientLanguage} className="language-select">
          <option value="en">English</option>
          <option value="es">Spanish</option>
          <option value="zh">Mandarin</option>
          <option value="fr">French</option>
          <option value="ar">Arabic</option>
          <option value="vi">Vietnamese</option>
        </select>
      </div>

      <div className="transcript-display">
        {transcript.map((segment, idx) => (
          <div key={idx} className={`segment ${segment.speaker}`}>
            <span className="speaker-label">
              {segment.speaker === 'provider' ? '👨‍⚕️ You' : '🧑 Patient'}
            </span>
            <p className="original-text">{segment.originalText}</p>
            {segment.translatedText && (
              <p className="translated-text">{segment.translatedText}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
};
```

**Backend WebSocket for Real-Time Processing:**
```python
# backend/routers/transcription.py

from fastapi import WebSocket, APIRouter
from app.services.realtime_transcription import RealtimeTranscriber
from app.services.translation import TranslationService
from app.services.speaker_diarization import SpeakerDiarizer

router = APIRouter()
transcriber = RealtimeTranscriber()
translator = TranslationService()
diarizer = SpeakerDiarizer()

@router.websocket("/ws/transcribe")
async def websocket_transcribe(websocket: WebSocket, patient_language: str = "en"):
    await websocket.accept()
    
    try:
        while True:
            audio_chunk = await websocket.receive_bytes()
            
            # Transcribe
            transcription = await transcriber.transcribe_chunk(audio_chunk)
            
            # Identify speaker
            speaker = await diarizer.identify_speaker(audio_chunk)
            
            # Translate if needed
            if speaker == 'patient' and transcription['language'] != 'en':
                translated_text = await translator.translate(
                    transcription['text'],
                    from_lang=transcription['language'],
                    to_lang='en'
                )
            else:
                translated_text = transcription['text']
            
            segment = {
                "speaker": speaker,
                "originalText": transcription['text'],
                "translatedText": translated_text,
                "language": transcription['language'],
                "timestamp": datetime.now().isoformat()
            }
            
            await websocket.send_json(segment)
    
    except Exception as e:
        await websocket.send_json({"error": str(e)})
        await websocket.close()
```

---

### 2. Automatic Chart Element Extraction

```python
# backend/services/chart_extraction.py

async def extract_chart_elements_from_transcript(
    transcript: str
) -> dict:
    """Auto-extract HPI, ROS, PEx from transcript."""
    
    client = AsyncOpenAI()
    
    extraction_prompt = f"""
Extract chart elements. Return ONLY JSON:
{{
  "chief_complaint": "string",
  "hpi": "string",
  "ros": "string",
  "physical_exam": "string"
}}

Transcript: {transcript}
"""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": extraction_prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    return json.loads(response.choices[0].message.content)
```

---

### 3. Procedure Auto-Population with Voice Commands

```python
# backend/routers/procedures.py

@router.post("/api/procedures/insert/{procedure_name}")
async def insert_procedure_note(
    procedure_name: str,
    encounter_id: str,
    current_user: User = Depends(get_current_user)
):
    """Generate customized procedure note from voice command."""
    
    template = db.query(ProcedureTemplate).filter(
        ProcedureTemplate.procedure_name.ilike(f"%{procedure_name}%")
    ).first()
    
    if not template:
        return {"error": f"Procedure '{procedure_name}' not found"}
    
    encounter = db.query(PatientEncounter).filter(
        PatientEncounter.encounter_id == encounter_id
    ).first()
    
    customized_note = await generate_procedure_note(
        base_template=template.base_template,
        encounter_data=encounter
    )
    
    return {
        "procedure_name": procedure_name,
        "generated_note": customized_note,
        "requires_review": True
    }

async def generate_procedure_note(base_template: str, encounter_data) -> str:
    """Customize generic procedure template with encounter specifics."""
    
    client = AsyncOpenAI()
    
    prompt = f"""
Customize this procedure template with encounter details:

Template:
{base_template}

Patient age: {encounter_data.patient_age}
Vitals: BP {encounter_data.vitals_bp}, HR {encounter_data.vitals_hr}

Return ONLY customized note text. No markdown.
"""
    
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )
    
    return response.choices[0].message.content
```

---

### 4. Fewest Clicks Design

**Current Flow (Friend's App):**
```
1. Open app
2. Press record
3. (Encounter)
4. Stop recording
5. Wait for transcription
6. Select sections manually
7. Generate note
8. Copy each section
9. Paste into Epic
10. Add procedures manually
= 10+ clicks
```

**Adelyn Flow:**
```
1. Tap "Start Listening" (1 click)
2. (Do your job - auto-transcribe, auto-translate, auto-extract)
3. Say "Insert laceration repair" (1 voice command)
4. Say "Generate chart" (1 voice command)
5. Review (read-only)
6. Tap "Copy Full Chart" (1 click)
7. Paste into Epic
= 3-4 clicks, zero manual work
```

---

## MVP Timeline: 8 Weeks

### Week 1-2: Local Dev Setup
- [ ] Docker Compose with SQL Server, FastAPI, React
- [ ] Auth system working
- [ ] Database initialized

### Week 3-4: Real-Time Audio
- [ ] Whisper transcription
- [ ] Azure Translator
- [ ] Speaker diarization
- [ ] Live transcript display

### Week 5-6: Chart Extraction & Procedures
- [ ] Auto-extract HPI, ROS, PEx
- [ ] Procedure templates
- [ ] Voice command recognition
- [ ] Procedure generation

### Week 7-8: Polish
- [ ] Your M365 MDM prompt integrated
- [ ] Full chart export
- [ ] UI/UX refinement
- [ ] Testing with real cases

---

## Ready for Docker Setup?

I'll now create:

✅ `docker-compose.yml` (SQL Server + FastAPI + React)
✅ FastAPI starter with all endpoints
✅ React PWA with clean minimal UI
✅ Database schema pre-loaded
✅ README with 5-minute setup

**Let's build this. 🚀**
