Write-Host "Starting MediAssist AI Backend (FastAPI)..." -ForegroundColor Cyan
$env:PYTHONPATH = "backend"
& "backend\venv\Scripts\python.exe" -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

