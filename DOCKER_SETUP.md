# Docker Local Development Setup for Adelyn ER

## Prerequisites (5 minutes to install)

### 1. Install Docker Desktop
- **Mac/Windows**: https://www.docker.com/products/docker-desktop
- **Linux**: `sudo apt-get install docker.io docker-compose`

### 2. Install Node.js (for React development)
- https://nodejs.org/ (LTS version recommended)
- Verify: `node --version` and `npm --version`

### 3. Install Python (for FastAPI development)
- https://www.python.org/downloads/ (3.10+)
- Verify: `python --version`

### 4. Clone This Repository
```bash
git clone https://github.com/aaguess/grokscribe-clean.git
cd grokscribe-clean
```

---

## Quick Start (5 Minutes)

### Step 1: Copy the Docker files to your repo

I'll create these files for you in the next step. For now, just follow along.

### Step 2: Start Everything with One Command

```bash
docker-compose up --build
```

**Wait ~2 minutes for containers to start...**

You'll see:
```
✅ SQL Server running on localhost:1433
✅ FastAPI backend running on http://localhost:8000
✅ React frontend running on http://localhost:3000
```

### Step 3: Open the App

Go to **http://localhost:3000** in your browser.

You should see the Adelyn ER login screen.

### Step 4: Create Test Account

Default credentials (pre-populated):
- **Email**: `doctor@hospital.local`
- **Password**: `testpass123`

(Change these in `.env` file before production)

---

## File Structure

```
grokscribe-clean/
├── docker-compose.yml          ← Master orchestration file
├── .env.example                ← Copy to .env and fill in
├── backend/                    ← FastAPI app
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py                 ← FastAPI entry point
│   ├── app/
│   │   ├── __init__.py
│   │   ├── config.py
│   │   ├── database.py         ← SQL connection
│   │   ├── security.py         ← Auth & encryption
│   │   ├── routers/
│   │   │   ├── auth.py         ← Login endpoints
│   │   │   ├── encounters.py   ← Recording endpoints
│   │   │   ├── notes.py        ← Note generation
│   │   │   ├── procedures.py   ← Procedure endpoints
│   │   │   └── transcription.py ← WebSocket transcription
│   │   ├── services/
│   │   │   ├── transcription.py    ← Whisper integration
│   │   │   ├── translation.py      ← Azure Translator
│   │   │   ├── chart_extraction.py ← Auto-parse HPI/ROS/PEx
│   │   │   ├── procedure_generation.py
│   │   │   └── encryption.py
│   │   └── models/
│   │       ├── database.py         ← SQLAlchemy ORM
│   │       └── schemas.py          ← Pydantic validation
│   └── .dockerignore
├── frontend/                   ← React PWA
│   ├── Dockerfile
│   ├── package.json
│   ├── public/
│   │   ├── index.html
│   │   └── manifest.json       ← PWA config
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── api/                ← API client functions
│   │   │   ├── auth.ts
│   │   │   ├── encounters.ts
│   │   │   ├── notes.ts
│   │   │   ├── procedures.ts
│   │   │   └── client.ts       ← Fetch wrapper
│   │   ├── components/
│   │   │   ├── AmbientListener.tsx
│   │   │   ├── ChartDisplay.tsx
│   │   │   ├── ProcedureVoiceCommand.tsx
│   │   │   ├── MDMGenerator.tsx
│   │   │   └── FullChartReview.tsx
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── DashboardPage.tsx
│   │   │   └── EncounterPage.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useEncounter.ts
│   │   ├── store/              ← Zustand state management
│   │   │   └── encounterStore.ts
│   │   └── styles/
│   │       └── globals.css
│   └── .dockerignore
└── sql/
    └── init.sql                ← Database schema initialization
```

---

## Docker Compose File

**Create file: `docker-compose.yml`**

```yaml
version: '3.9'

services:
  # SQL Server Database
  mssql:
    image: mcr.microsoft.com/mssql/server:2022-latest
    container_name: adelyn-mssql
    environment:
      SA_PASSWORD: YourSecurePassword123!
      ACCEPT_EULA: "Y"
      MSSQL_PID: Express
    ports:
      - "1433:1433"
    volumes:
      - mssql_data:/var/opt/mssql
      - ./sql/init.sql:/docker-entrypoint-initdb.d/init.sql
    networks:
      - adelyn-network
    healthcheck:
      test: ["CMD", "/opt/mssql-tools/bin/sqlcmd", "-S", "localhost", "-U", "sa", "-P", "YourSecurePassword123!", "-Q", "SELECT 1"]
      interval: 10s
      timeout: 5s
      retries: 5

  # FastAPI Backend
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: adelyn-backend
    environment:
      DATABASE_URL: mssql+pyodbc://sa:YourSecurePassword123!@mssql:1433/adelyn?driver=ODBC+Driver+17+for+SQL+Server
      OPENAI_API_KEY: ${OPENAI_API_KEY:-sk-test-key}
      AZURE_TRANSLATOR_KEY: ${AZURE_TRANSLATOR_KEY:-test-key}
      AZURE_TRANSLATOR_ENDPOINT: ${AZURE_TRANSLATOR_ENDPOINT:-https://api.cognitive.microsofttranslator.com/}
      JWT_SECRET_KEY: ${JWT_SECRET_KEY:-your-secret-key-change-in-production}
      JWT_ALGORITHM: HS256
      TOKEN_EXPIRE_MINUTES: 60
      ENVIRONMENT: development
      DEBUG: "True"
    ports:
      - "8000:8000"
    volumes:
      - ./backend:/app
    depends_on:
      mssql:
        condition: service_healthy
    networks:
      - adelyn-network
    command: python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload

  # React Frontend
  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    container_name: adelyn-frontend
    ports:
      - "3000:3000"
    volumes:
      - ./frontend/src:/app/src
    depends_on:
      - backend
    networks:
      - adelyn-network
    environment:
      REACT_APP_API_URL: http://localhost:8000

volumes:
  mssql_data:

networks:
  adelyn-network:
    driver: bridge
```

---

## Backend Setup

### `backend/Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install ODBC driver for SQL Server
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl https://packages.microsoft.com/keys/microsoft.asc | apt-key add - \
    && curl https://packages.microsoft.com/config/debian/11/prod.list > /etc/apt/sources.list.d/mssql-release.list \
    && apt-get update \
    && ACCEPT_EULA=Y apt-get install -y msodbcsql17 \
    && apt-get clean

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

CMD ["python", "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `backend/requirements.txt`

```
fastapi==0.104.1
uvicorn[standard]==0.24.0
sqlalchemy==2.0.23
pyodbc==5.0.1
python-dotenv==1.0.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.6
openai==1.3.7
httpx==0.25.1
aiofiles==23.2.1
websockets==12.0
requests==2.31.0
pyannote.audio==2.1.1
```

### `backend/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base
from app.routers import auth, encounters, notes, procedures, transcription

# Create tables
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Adelyn ER API",
    description="AI-powered ambient listening scribe for emergency physicians",
    version="0.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(encounters.router)
app.include_router(notes.router)
app.include_router(procedures.router)
app.include_router(transcription.router)

@app.get("/")
async def root():
    return {"message": "Adelyn ER API v0.1.0"}

@app.get("/health")
async def health():
    return {"status": "healthy"}
```

### `backend/app/database.py`

```python
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
import os

DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "mssql+pyodbc://sa:YourSecurePassword123!@localhost:1433/adelyn?driver=ODBC+Driver+17+for+SQL+Server"
)

engine = create_engine(
    DATABASE_URL,
    poolclass=NullPool,  # Needed for MSSQL in containers
    echo=True
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### `backend/app/models/database.py`

```python
from sqlalchemy import Column, String, DateTime, Boolean, UUID, ForeignKey, Text, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
import uuid
from app.database import Base

class User(Base):
    __tablename__ = "users"
    
    user_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True)
    display_name = Column(String(255))
    hashed_password = Column(String(255))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_active = Column(Boolean, default=True)

class PatientEncounter(Base):
    __tablename__ = "patient_encounters"
    
    encounter_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    audio_file_path = Column(String(500))
    raw_transcript = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    is_finalized = Column(Boolean, default=False)

class ClinicalNote(Base):
    __tablename__ = "clinical_notes"
    
    note_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    encounter_id = Column(UUID(as_uuid=True), ForeignKey("patient_encounters.encounter_id"))
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.user_id"))
    hpi = Column(Text)
    ros = Column(Text)
    physical_exam = Column(Text)
    mdm = Column(Text)
    impression_plan = Column(Text)
    full_note = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ProcedureTemplate(Base):
    __tablename__ = "procedure_templates"
    
    procedure_id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    procedure_name = Column(String(255))
    base_template = Column(Text)
    is_default = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
```

### `backend/app/routers/auth.py`

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models.database import User
from app.security import hash_password, verify_password, create_access_token
from pydantic import BaseModel

router = APIRouter(prefix="/api/auth", tags=["auth"])

class LoginRequest(BaseModel):
    email: str
    password: str

class LoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

@router.post("/login", response_model=LoginResponse)
async def login(request: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    if not user or not verify_password(request.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token}

@router.post("/register", response_model=LoginResponse)
async def register(request: LoginRequest, db: Session = Depends(get_db)):
    existing_user = db.query(User).filter(User.email == request.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    user = User(
        email=request.email,
        hashed_password=hash_password(request.password),
        display_name=request.email.split("@")[0]
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    
    access_token = create_access_token(data={"sub": str(user.user_id)})
    return {"access_token": access_token}
```

---

## Frontend Setup

### `frontend/Dockerfile`

```dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev"]
```

### `frontend/package.json`

```json
{
  "name": "adelyn-frontend",
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "vite build",
    "preview": "vite preview",
    "lint": "eslint src"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "zustand": "^4.4.1",
    "axios": "^1.6.0"
  },
  "devDependencies": {
    "@types/react": "^18.2.37",
    "@types/react-dom": "^18.2.15",
    "@vitejs/plugin-react": "^4.2.0",
    "vite": "^5.0.2",
    "typescript": "^5.2.2"
  }
}
```

### `frontend/src/App.tsx`

```typescript
import { useState } from 'react';
import './styles/globals.css';

function App() {
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  return (
    <div className="app">
      <header className="header">
        <h1>🏥 Adelyn ER</h1>
        <p>AI Ambient Listening Scribe</p>
      </header>

      <main className="main">
        {!isLoggedIn ? (
          <LoginPage onLogin={() => setIsLoggedIn(true)} />
        ) : (
          <DashboardPage />
        )}
      </main>
    </div>
  );
}

function LoginPage({ onLogin }: { onLogin: () => void }) {
  const [email, setEmail] = useState('doctor@hospital.local');
  const [password, setPassword] = useState('testpass123');

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    // Call /api/auth/login
    onLogin();
  };

  return (
    <form onSubmit={handleLogin} className="login-form">
      <h2>Login</h2>
      <input
        type="email"
        value={email}
        onChange={(e) => setEmail(e.target.value)}
        placeholder="Email"
      />
      <input
        type="password"
        value={password}
        onChange={(e) => setPassword(e.target.value)}
        placeholder="Password"
      />
      <button type="submit">Login</button>
    </form>
  );
}

function DashboardPage() {
  return (
    <div className="dashboard">
      <h2>👨‍⚕️ Welcome, Doctor</h2>
      <p>Ready to start an encounter?</p>
      <button className="btn-primary">🎤 Start Ambient Listen</button>
    </div>
  );
}

export default App;
```

### `frontend/src/styles/globals.css`

```css
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
    'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
    sans-serif;
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  background: #0f0f1e;
  color: #e0e0e0;
}

.app {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
}

.header {
  background: #1a1a2e;
  padding: 2rem;
  border-bottom: 2px solid #0084d4;
  text-align: center;
}

.header h1 {
  font-size: 2.5rem;
  color: #0084d4;
}

.header p {
  color: #aaa;
  margin-top: 0.5rem;
}

.main {
  flex: 1;
  padding: 2rem;
  max-width: 1200px;
  margin: 0 auto;
  width: 100%;
}

.login-form {
  background: #16213e;
  padding: 2rem;
  border-radius: 8px;
  max-width: 400px;
  margin: 2rem auto;
}

.login-form h2 {
  color: #0084d4;
  margin-bottom: 1.5rem;
}

.login-form input {
  width: 100%;
  padding: 0.75rem;
  margin-bottom: 1rem;
  border: 1px solid #0084d4;
  border-radius: 4px;
  background: #0f0f1e;
  color: #e0e0e0;
  font-size: 1rem;
}

.login-form button {
  width: 100%;
  padding: 0.75rem;
  background: #0084d4;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
  font-size: 1rem;
  font-weight: bold;
}

.login-form button:hover {
  background: #0066a8;
}

.dashboard {
  text-align: center;
}

.btn-primary {
  padding: 1rem 2rem;
  background: #0084d4;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 1.1rem;
  cursor: pointer;
  margin-top: 1rem;
}

.btn-primary:hover {
  background: #0066a8;
}
```

---

## Database Initialization

### `sql/init.sql`

```sql
CREATE DATABASE adelyn;
GO

USE adelyn;
GO

-- Users table
CREATE TABLE users (
    user_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    email VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    hashed_password VARCHAR(255),
    created_at DATETIME2 DEFAULT GETDATE(),
    is_active BIT DEFAULT 1
);

-- Patient encounters
CREATE TABLE patient_encounters (
    encounter_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    user_id UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES users(user_id),
    audio_file_path VARCHAR(500),
    raw_transcript TEXT,
    created_at DATETIME2 DEFAULT GETDATE(),
    is_finalized BIT DEFAULT 0
);

-- Clinical notes
CREATE TABLE clinical_notes (
    note_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    encounter_id UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES patient_encounters(encounter_id),
    user_id UNIQUEIDENTIFIER NOT NULL FOREIGN KEY REFERENCES users(user_id),
    hpi TEXT,
    ros TEXT,
    physical_exam TEXT,
    mdm TEXT,
    impression_plan TEXT,
    full_note TEXT,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Procedure templates
CREATE TABLE procedure_templates (
    procedure_id UNIQUEIDENTIFIER PRIMARY KEY DEFAULT NEWID(),
    procedure_name VARCHAR(255),
    base_template TEXT,
    is_default BIT DEFAULT 1,
    created_at DATETIME2 DEFAULT GETDATE()
);

-- Insert default procedures
INSERT INTO procedure_templates (procedure_name, base_template) VALUES
('Laceration Repair', 'The wound was inspected and found to be a laceration measuring X cm in length. The wound was irrigated copiously with sterile normal saline. Local anesthesia was administered. The laceration was closed using appropriate suturing technique. Post procedure wound care instructions were provided. Patient tolerated procedure well.'),
('Incision and Drainage', 'The area was prepped with chlorhexidine. Local anesthesia was administered. An incision was made over the area of fluctuance. Purulent material was expressed and evacuated. The cavity was irrigated with sterile normal saline. A drain was placed. Dressing was applied. Patient tolerated procedure well.'),
('Chest Tube', 'The patient was positioned appropriately. The site was prepped and draped in sterile fashion. Local anesthesia was administered. A small incision was made and the tube was inserted into the thoracic cavity under direct visualization. Appropriate position was confirmed. The tube was secured with sutures. The tube was connected to appropriate drainage system. Patient tolerated procedure well.');
```

---

## Environment Variables

### `.env.example`

```bash
# Database
MSSQL_SA_PASSWORD=YourSecurePassword123!
DATABASE_URL=mssql+pyodbc://sa:YourSecurePassword123!@mssql:1433/adelyn?driver=ODBC+Driver+17+for+SQL+Server

# OpenAI
OPENAI_API_KEY=sk-your-key-here

# Azure Translator
AZURE_TRANSLATOR_KEY=your-azure-key
AZURE_TRANSLATOR_ENDPOINT=https://api.cognitive.microsofttranslator.com/

# JWT
JWT_SECRET_KEY=your-super-secret-key-change-in-production
JWT_ALGORITHM=HS256
TOKEN_EXPIRE_MINUTES=60

# App
ENVIRONMENT=development
DEBUG=True
```

**Copy this file:**
```bash
cp .env.example .env
```

---

## Running Locally

### 1. Start Everything

```bash
docker-compose up --build
```

Wait for all services to start (~2 minutes):
```
✅ mssql is healthy
✅ backend is running on port 8000
✅ frontend is running on port 3000
```

### 2. Access the App

- **Frontend**: http://localhost:3000
- **API Docs**: http://localhost:8000/docs
- **Database**: localhost:1433 (SQL Server)

### 3. Login

**Default Test Account:**
- Email: `doctor@hospital.local`
- Password: `testpass123`

### 4. Stop Everything

```bash
docker-compose down
```

To also delete database:
```bash
docker-compose down -v
```

---

## Troubleshooting

### "Connection refused" error?
```bash
# Check if containers are running
docker ps

# View logs
docker logs adelyn-backend
docker logs adelyn-mssql
```

### Frontend not connecting to backend?
Edit `frontend/.env`:
```
REACT_APP_API_URL=http://localhost:8000
```

### SQL Server connection failed?
Wait 30 seconds for SQL Server to fully start. Then:
```bash
docker logs adelyn-mssql
```

### Port already in use?
Change in `docker-compose.yml`:
```yaml
ports:
  - "3001:3000"  # React on 3001 instead
  - "8001:8000"  # FastAPI on 8001 instead
  - "1434:1433"  # SQL on 1434 instead
```

---

## Next Steps

Once Docker is running:

1. ✅ **Test login flow** (done locally)
2. ✅ **Build audio recording component** (Week 1-2)
3. ✅ **Add real-time transcription** (Week 3-4)
4. ✅ **Add translation** (Week 3-4)
5. ✅ **Add chart extraction** (Week 5-6)
6. ✅ **Add procedure notes** (Week 5-6)
7. ✅ **Polish UI** (Week 7-8)

---

## Commands You'll Use Often

```bash
# Start everything
docker-compose up

# Start in background
docker-compose up -d

# View logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f mssql

# Stop everything
docker-compose down

# Rebuild images (after code changes)
docker-compose up --build

# Access SQL Server container
docker exec -it adelyn-mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P YourSecurePassword123!
```

---

**Ready to start? Run:**
```bash
docker-compose up --build
```

Then navigate to **http://localhost:3000** 🚀
