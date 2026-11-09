Write-Host "Seeding MediAssist AI Database with Clinical Cases..." -ForegroundColor Cyan
$env:PYTHONPATH = "backend"
& "backend\venv\Scripts\python.exe" backend\app\seed_data.py

