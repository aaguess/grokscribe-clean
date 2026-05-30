# Adelyn ER - Local Development Setup

## Quick Start (5 Minutes)

### Prerequisites
- Docker Desktop installed: https://www.docker.com/products/docker-desktop
- Node.js installed: https://nodejs.org/
- Python 3.10+ installed: https://www.python.org/

### Start the App

```bash
# Clone and navigate to repo
git clone https://github.com/aaguess/grokscribe-clean.git
cd grokscribe-clean

# Start all services with Docker
docker-compose up --build
```

Wait 2-3 minutes for containers to start...

### Access the App

- **Frontend**: http://localhost:5173
- **API Docs**: http://localhost:8000/docs
- **API Health**: http://localhost:8000/health

### Login

**Test Account:**
- Email: `doctor@hospital.local`
- Password: `testpass123`

### Stop Everything

```bash
docker-compose down
```

---

## Architecture

```
Frontend (React PWA)     →  Backend (FastAPI)     →  Database (SQL Server)
http://localhost:5173      http://localhost:8000      localhost:1433
```

---

## File Structure

```
grokscribe-clean/
├── docker-compose.yml              # Orchestration
├── .env                            # Environment variables
├── backend/                        # FastAPI backend
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── main.py
│   └── app/
│       ├── database.py
│       ├── security.py
│       ├── models/
│       ├── routers/
│       └── services/
├── frontend/                       # React PWA
│   ├── Dockerfile
│   ├── package.json
│   ├── vite.config.ts
│   ├── public/
│   └── src/
│       ├── App.tsx
│       ├── main.tsx
│       └── styles/
└── sql/
    └── init.sql                    # Database schema
```

---

## Development Workflow

### Backend Development
```bash
# Backend code is automatically reloaded when you edit
# Edit files in backend/app/* and changes appear instantly

# View backend logs
docker logs adelyn-backend -f
```

### Frontend Development
```bash
# Frontend hot-reloads on save
# Edit files in frontend/src/* and changes appear instantly

# View frontend logs
docker logs adelyn-frontend -f
```

### Database Access
```bash
# Connect to SQL Server
docker exec -it adelyn-mssql /opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P YourSecurePassword123!

# Query
SELECT * FROM procedure_templates;
```

---

## Common Commands

```bash
# Start in background
docker-compose up -d

# View all logs
docker-compose logs -f

# Rebuild after dependency changes
docker-compose up --build

# Stop and remove containers
docker-compose down

# Stop and remove all data
docker-compose down -v

# View container status
docker ps
```

---

## Troubleshooting

### Port Already in Use
```bash
# Change in docker-compose.yml
# Frontend: "3001:5173"
# Backend: "8001:8000"
# Database: "1434:1433"
```

### SQL Server Won't Start
```bash
# Wait 30 seconds and check logs
docker logs adelyn-mssql

# Restart
docker-compose restart mssql
```

### Frontend Can't Connect to Backend
```bash
# Check docker network
docker network ls

# Verify containers are on same network
docker inspect adelyn-frontend
```

### "Connection refused" Error
```bash
# Ensure all containers are running
docker ps

# Rebuild
docker-compose down -v
docker-compose up --build
```

---

## Next Steps

1. ✅ App is running locally
2. 📝 Next: Build real-time audio recording
3. 🎤 Then: Add transcription integration
4. 🌍 Then: Add translation
5. 📋 Then: Add chart extraction
6. 🔧 Then: Add procedure notes

---

## Notes

- Frontend port is **5173** (Vite default), not 3000
- API runs on **8000**
- SQL Server runs on **1433**
- Test user is pre-created: `doctor@hospital.local` / `testpass123`
- All code changes auto-reload (no need to restart containers)

---

Need help? Check the main documentation files:
- `DOCKER_SETUP.md` - Detailed Docker setup
- `ADELYN_FEATURES.md` - Feature overview
- `PRODUCTION_SPEC.md` - Production architecture
- `OFFLINE_ARCHITECTURE.md` - Offline-first design
