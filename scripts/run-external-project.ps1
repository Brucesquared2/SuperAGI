param(
    [Parameter(Mandatory = $true)]
    [string]$ProjectName,

    [ValidateSet("setup", "run", "both")]
    [string]$Mode = "both",

    [string]$ManifestPath = "external-projects.json"
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Load-Project {
    param(
        [string]$Path,
        [string]$Name
    )

    if (-not (Test-Path $Path)) {
        throw "Manifest file not found: $Path"
    }

    $manifest = Get-Content -Raw -Path $Path | ConvertFrom-Json
    if (-not $manifest.projects) {
        throw "Manifest must contain a 'projects' array."
    }

    $project = $manifest.projects | Where-Object { $_.name -eq $Name } | Select-Object -First 1
    if (-not $project) {
        throw "Project '$Name' was not found in $Path"
    }

    return $project
}

function Test-CommandExists {
    param([string]$Name)
    return [bool](Get-Command $Name -ErrorAction SilentlyContinue)
}

function Invoke-SafeCommand {
    param(
        [string]$Command,
        [string]$WorkingDirectory
    )

    Write-Host ("exec  {0}" -f $Command)
    Push-Location $WorkingDirectory
    try {
        $global:LASTEXITCODE = 0
        Invoke-Expression $Command
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed with exit code ${LASTEXITCODE}: $Command"
        }
    }
    finally {
        Pop-Location
    }
}

function Resolve-SetupCommand {
    param([string]$ProjectPath)

    if (Test-Path (Join-Path $ProjectPath "pnpm-lock.yaml")) {
        if (-not (Test-CommandExists "pnpm")) {
            throw "Detected pnpm project but 'pnpm' is not installed."
        }
        return "pnpm install"
    }

    if (Test-Path (Join-Path $ProjectPath "yarn.lock")) {
        if (-not (Test-CommandExists "yarn")) {
            throw "Detected yarn project but 'yarn' is not installed."
        }
        return "yarn install"
    }

    if (Test-Path (Join-Path $ProjectPath "package.json")) {
        if (-not (Test-CommandExists "npm")) {
            throw "Detected npm project but 'npm' is not installed."
        }
        return "npm install"
    }

    if (Test-Path (Join-Path $ProjectPath "pyproject.toml")) {
        if (Test-CommandExists "uv") {
            return "uv sync"
        }
        if (Test-CommandExists "pip") {
            return "pip install -e ."
        }
        throw "Detected Python project but neither 'uv' nor 'pip' is available."
    }

    if (Test-Path (Join-Path $ProjectPath "requirements.txt")) {
        if (-not (Test-CommandExists "pip")) {
            throw "Detected requirements.txt but 'pip' is not available."
        }
        return "pip install -r requirements.txt"
    }

    throw "Could not infer setup command for $ProjectPath. Set setup_command in external-projects.json."
}

function Resolve-RunCommand {
    param([string]$ProjectPath)

    if (Test-Path (Join-Path $ProjectPath "pnpm-lock.yaml")) {
        return "pnpm run dev"
    }

    if (Test-Path (Join-Path $ProjectPath "yarn.lock")) {
        return "yarn dev"
    }

    if (Test-Path (Join-Path $ProjectPath "package.json")) {
        return "npm run dev"
    }

    if (Test-Path (Join-Path $ProjectPath "pyproject.toml")) {
        if (Test-CommandExists "uv") {
            return "uv run python -m app"
        }
        return "python -m app"
    }

    throw "Could not infer run command for $ProjectPath. Set run_command in external-projects.json."
}

$project = Load-Project -Path $ManifestPath -Name $ProjectName
$projectPath = $project.path

if ([string]::IsNullOrWhiteSpace($projectPath)) {
    throw "Project '$ProjectName' has empty path."
}

if (-not (Test-Path $projectPath)) {
    throw "Project path does not exist: $projectPath. Run sync first."
}

if ($Mode -eq "setup" -or $Mode -eq "both") {
    $setupCommand = if ([string]::IsNullOrWhiteSpace($project.setup_command)) {
        Resolve-SetupCommand -ProjectPath $projectPath
    } else {
        $project.setup_command
    }
    Invoke-SafeCommand -Command $setupCommand -WorkingDirectory $projectPath
}

if ($Mode -eq "run" -or $Mode -eq "both") {
    $runCommand = if ([string]::IsNullOrWhiteSpace($project.run_command)) {
        Resolve-RunCommand -ProjectPath $projectPath
    } else {
        $project.run_command
    }
    Invoke-SafeCommand -Command $runCommand -WorkingDirectory $projectPath
}
