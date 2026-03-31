@echo off
echo Starting Digital Twin System...

start "Digital Twin Backend" cmd /k "cd backend && python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
start "Digital Twin Frontend" cmd /k "cd frontend && npm run dev"

echo System started.
echo Backend running on http://localhost:8000
echo Frontend running on http://localhost:5173
pause
