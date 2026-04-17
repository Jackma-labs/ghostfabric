$patterns = @(
  @{ Name = "api_key"; Regex = 'sk-[A-Za-z0-9_-]{8,}' },
  @{ Name = "private_key"; Regex = 'BEGIN (RSA|OPENSSH|EC|DSA) PRIVATE KEY' },
  @{ Name = "bearer_header"; Regex = 'Authorization:\s*Bearer\s+[A-Za-z0-9._-]{8,}' },
  @{ Name = "ssh_target"; Regex = 'root@[A-Za-z0-9_.-]+' },
  @{ Name = "windows_user_path"; Regex = 'C:\\Users\\[^\\]+' },
  @{ Name = "linux_home_path"; Regex = '/home/[A-Za-z0-9_.-]+' },
  @{ Name = "ssh_key_name"; Regex = 'KeyPair-[A-Za-z0-9_.-]+' },
  @{ Name = "public_ip"; Regex = '\b(?!(127\.0\.0\.1|0\.0\.0\.0)\b)\d{1,3}(?:\.\d{1,3}){3}\b' }
)

$excludePatterns = @(
  '\\.git\\',
  '\\__pycache__\\',
  '\.pyc$',
  'scripts\\secret_scan\.ps1$'
)

$files = Get-ChildItem -Recurse -File -ErrorAction SilentlyContinue | Where-Object {
  $path = $_.FullName
  -not ($excludePatterns | Where-Object { $path -match $_ })
}

$findings = @()
foreach ($file in $files) {
  $lineNo = 0
  foreach ($line in Get-Content -LiteralPath $file.FullName -ErrorAction SilentlyContinue) {
    $lineNo += 1
    foreach ($pattern in $patterns) {
      if ($line -match $pattern.Regex) {
        $findings += [PSCustomObject]@{
          Path = $file.FullName
          LineNumber = $lineNo
          Pattern = $pattern.Name
          Line = $line.Trim()
        }
      }
    }
  }
}

if ($findings.Count -gt 0) {
  $findings | ForEach-Object {
    "{0}:{1}:{2}:{3}" -f $_.Path, $_.LineNumber, $_.Pattern, $_.Line
  }
  exit 1
}

Write-Host "No obvious secrets found."
