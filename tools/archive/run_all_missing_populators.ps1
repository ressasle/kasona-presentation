Write-Host "========================================="
Write-Host "Starting Kasona Mass Population Process"
Write-Host "========================================="

Write-Host "`n[1/4] Remediating Missing English Pillars..."
python tools/remediate_all_pillars.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error in remediate_all_pillars.py" }

Write-Host "`n[2/4] Generating Missing English Artifacts (Markdown/PDF/Audio)..."
python tools/fill_all_missing_english_artifacts.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error in fill_all_missing_english_artifacts.py" }

Write-Host "`n[3/4] Translating Content to German..."
python tools/populate_german_content.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error in populate_german_content.py" }

Write-Host "`n[4/4] Generating Missing German Artifacts (Markdown/PDF/Audio)..."
python tools/fill_all_missing_german_artifacts.py
if ($LASTEXITCODE -ne 0) { Write-Host "Error in fill_all_missing_german_artifacts.py" }

Write-Host "`n========================================="
Write-Host "ALL MASS POPULATION PROCESSES COMPLETED"
Write-Host "========================================="
