param(
    [ValidateSet("init", "update", "status")]
    [string]$Action = "init",

    [string]$ManifestPath = "external-projects.json",

    [switch]$IncludeDisabled
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

function Assert-GitAvailable {
    if (-not (Get-Command git -ErrorAction SilentlyContinue)) {
        throw "git is required but was not found in PATH."
    }
}

function Load-Manifest {
    param([string]$Path)

    if (-not (Test-Path $Path)) {
        throw "Manifest file not found: $Path"
    }

    $content = Get-Content -Raw -Path $Path | ConvertFrom-Json
    if (-not $content.projects) {
        throw "Manifest must contain a 'projects' array."
    }

    return $content.projects
}

function Ensure-ParentDirectory {
    param([string]$ProjectPath)

    $parent = Split-Path -Parent $ProjectPath
    if ([string]::IsNullOrWhiteSpace($parent)) {
        return
    }

    if (-not (Test-Path $parent)) {
        New-Item -ItemType Directory -Path $parent | Out-Null
    }
}

function Project-IsSubmodule {
    param([string]$ProjectPath)

    $gitmodules = ".gitmodules"
    if (-not (Test-Path $gitmodules)) {
        return $false
    }

    $normalized = $ProjectPath -replace "\\", "/"
    $match = git config -f $gitmodules --get-regexp "submodule\..*\.path" 2>$null |
        Select-String -Pattern (" {0}$" -f [regex]::Escape($normalized))

    return ($null -ne $match)
}

function Sync-Project {
    param(
        [pscustomobject]$Project,
        [string]$Mode
    )

    if (-not $IncludeDisabled -and -not $Project.enabled) {
        Write-Host ("skip  {0} (disabled)" -f $Project.name)
        return
    }

    if ([string]::IsNullOrWhiteSpace($Project.repo_url)) {
        Write-Host ("skip  {0} (repo_url is empty)" -f $Project.name)
        return
    }

    $path = $Project.path
    if ([string]::IsNullOrWhiteSpace($path)) {
        Write-Host ("skip  {0} (path is empty)" -f $Project.name)
        return
    }

    Ensure-ParentDirectory -ProjectPath $path
    $isSubmodule = Project-IsSubmodule -ProjectPath $path

    switch ($Mode) {
        "init" {
            if ($isSubmodule) {
                Write-Host ("init  {0} -> {1}" -f $Project.name, $path)
                git submodule update --init --recursive -- $path
                return
            }

            if (Test-Path $path) {
                Write-Host ("skip  {0} (path exists and is not a submodule): {1}" -f $Project.name, $path)
                return
            }

            $branch = if ([string]::IsNullOrWhiteSpace($Project.branch)) { "main" } else { $Project.branch }
            Write-Host ("add   {0} -> {1}" -f $Project.name, $path)
            git submodule add -b $branch $Project.repo_url $path
        }
        "update" {
            if (-not $isSubmodule) {
                Write-Host ("skip  {0} (not configured as submodule): {1}" -f $Project.name, $path)
                return
            }
            Write-Host ("pull  {0} -> {1}" -f $Project.name, $path)
            git submodule update --remote --merge -- $path
        }
        "status" {
            if (-not $isSubmodule) {
                Write-Host ("none  {0} (not configured as submodule): {1}" -f $Project.name, $path)
                return
            }
            git submodule status -- $path
        }
    }
}

Assert-GitAvailable
$projects = Load-Manifest -Path $ManifestPath

foreach ($project in $projects) {
    Sync-Project -Project $project -Mode $Action
}
