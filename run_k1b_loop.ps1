Set-Location C:\Users\lgnxu\ResearchRelated\tucc-chain-compile
$py = ".\.venv\Scripts\python.exe"
$stem = "h8_chain"
New-Item -ItemType Directory -Force -Path k1b | Out-Null
foreach ($arm in @("oracle_full", "cold", "pred", "b2", "oracle_content")) {
  $done = "k1b\${stem}_${arm}*_summary.json"
  if (Test-Path $done) { Write-Host "skip $arm -- already finished"; continue }
  $log = "k1b\${stem}_$arm.log"
  for ($i = 1; $i -le 100; $i++) {
    Add-Content -Path $log -Value "==== $(Get-Date -Format s) invocation $i arm $arm" -Encoding utf8
    & $py -u k1b_warmstart.py $stem --arm $arm --seed 0 --deadline 14400 2>&1 | Add-Content -Path $log -Encoding utf8
    if ($LASTEXITCODE -ne 0) { Write-Host "HALT: $arm exit code $LASTEXITCODE"; break }
    if (Test-Path $done) { Write-Host "finished $arm"; break }
  }
  if (-not (Test-Path $done)) { Write-Host "STOPPED before finishing $arm -- rerun to resume"; break }
}