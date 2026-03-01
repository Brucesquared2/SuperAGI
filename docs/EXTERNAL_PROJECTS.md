# External Projects

This repository can manage external projects as git submodules using:

- `external-projects.json` (manifest)
- `scripts/sync-external-projects.ps1` (sync script)
- `scripts/run-external-project.ps1` (setup/run script)

## Why this approach

- Keeps external code pinned to known commits.
- Keeps root history clean and updates explicit.
- Works for one project (`omnicore`) or many projects.

## Configure projects

Edit `external-projects.json`:

- `name`: display name
- `repo_url`: full git URL
- `path`: target folder inside this repo
- `branch`: branch used when first added
- `enabled`: set `true` to include

## Commands

From repo root (`C:\Users\bruce\SuperAGI`):

```powershell
# Add/init enabled projects as submodules
powershell -ExecutionPolicy Bypass -File .\scripts\sync-external-projects.ps1 -Action init

# Update enabled projects to latest remote commit on tracked branch
powershell -ExecutionPolicy Bypass -File .\scripts\sync-external-projects.ps1 -Action update

# Show submodule status for enabled projects
powershell -ExecutionPolicy Bypass -File .\scripts\sync-external-projects.ps1 -Action status
```

```powershell
# Setup and run a specific external project
powershell -ExecutionPolicy Bypass -File .\scripts\run-external-project.ps1 -ProjectName aaw-complete -Mode both
```

## Initial setup for omnicore

1. Set `repo_url` for the `omnicore` entry.
2. Keep `enabled: true`.
3. Run the init command.

## AAW-Complete quick start

1. Set `repo_url` for `aaw-complete` in `external-projects.json`.
2. Run:
   `powershell -ExecutionPolicy Bypass -File .\scripts\sync-external-projects.ps1 -Action init`
3. Run:
   `powershell -ExecutionPolicy Bypass -File .\scripts\run-external-project.ps1 -ProjectName aaw-complete -Mode both`
