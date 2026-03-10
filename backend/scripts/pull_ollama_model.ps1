# Pull LLaMA 3.2 3B Instruct model into Ollama
# PowerShell version

Write-Host "==================================================" -ForegroundColor Cyan
Write-Host "Pulling LLaMA 3.2 3B Instruct Model" -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "This will download ~2GB of data." -ForegroundColor Yellow
Write-Host "Please wait, this may take 5-10 minutes..." -ForegroundColor Yellow
Write-Host ""

# Pull the model
docker exec -it ollama ollama pull llama3.2:3b-instruct

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Model Pull Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Verifying model..." -ForegroundColor Cyan
docker exec -it ollama ollama list

Write-Host ""
Write-Host "Testing model..." -ForegroundColor Cyan
docker exec -it ollama ollama run llama3.2:3b-instruct "Say hello in one sentence"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Setup Complete!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Run: python seed_ollama_provider.py" -ForegroundColor White
Write-Host "2. Run: python test_ollama_provider.py" -ForegroundColor White
Write-Host "3. Test AI analysis with Ollama as fallback" -ForegroundColor White
