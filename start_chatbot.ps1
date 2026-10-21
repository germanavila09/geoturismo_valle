$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ChatbotDir = Join-Path $ProjectRoot "chatbot"

Set-Location $ProjectRoot

if (Get-Command python -ErrorAction SilentlyContinue) {
  $PythonCmd = "python"
} elseif (Get-Command py -ErrorAction SilentlyContinue) {
  $PythonCmd = "py"
} else {
  throw "No se encontro Python en el PATH. Abre PowerShell donde ya te funciono 'python scripts\run_all.py'."
}

Write-Host "Instalando/validando dependencias..." -ForegroundColor Green
& $PythonCmd -m pip install -r requirements.txt

Set-Location $ChatbotDir

Write-Host ""
Write-Host "GeoTurismo Chatbot API: http://localhost:8081" -ForegroundColor Green
Write-Host "Deja esta ventana abierta mientras uses el asistente." -ForegroundColor DarkGreen
Write-Host ""

& $PythonCmd -m uvicorn server:app --host 0.0.0.0 --port 8081 --reload
