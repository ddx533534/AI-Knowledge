param([switch]$Check)
$ErrorActionPreference = 'Stop'
$env:PYTHONIOENCODING = 'utf-8'
$candidates = @()
if ($env:CODEX_KNOWLEDGE_PYTHON) { $candidates += $env:CODEX_KNOWLEDGE_PYTHON }
$candidates += "$env:USERPROFILE\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe"
$candidates += @('python', 'python3', 'py')
foreach ($candidate in $candidates) {
    try {
        $version = & $candidate -c 'import sys; print(sys.version_info >= (3, 11))' 2>$null
        if ($LASTEXITCODE -eq 0 -and $version -eq 'True') {
            $arguments = @("$PSScriptRoot\install.py")
            if ($Check) { $arguments += '--check' }
            & $candidate @arguments
            exit $LASTEXITCODE
        }
    } catch { }
}
throw '安装工具需要 Python 3.11+；可通过 CODEX_KNOWLEDGE_PYTHON 指定运行时。'
