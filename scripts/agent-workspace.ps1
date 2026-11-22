param(
  [ValidateSet('codex','hermes')][string]$Agent = 'codex',
  [switch]$Check,
  [switch]$NewWindow
)
$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$command = Get-Command $Agent -ErrorAction SilentlyContinue
if ($Check) {
  $status = if ($null -eq $command) {'not installed'} else {'installed'}
  Write-Output "$Agent : $status ; repository=$repoRoot"
  exit 0
}
if ($null -eq $command) {
  throw "Agent '$Agent' is not installed on this Windows computer. Check docs/AI-TOOLCHAIN.md."
}
if ($NewWindow) {
  $target = '"' + $command.Source + '"'
  Start-Process -FilePath 'powershell.exe' -WorkingDirectory $repoRoot -ArgumentList @('-NoExit', '-NoProfile', '-Command', "& $target")
} else {
  Push-Location $repoRoot
  try { & $command.Source } finally { Pop-Location }
}
