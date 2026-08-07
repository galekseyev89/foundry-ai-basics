# Project Notes For AI Helpers

## Project overview

This is a small Azure AI Foundry practice app for AI-103 learning.

Keep changes simple and beginner friendly. Prefer clear functions, small modules,
and standard-library tools when possible.

## Tech stack

- Python 3.11+ package using the `src/` layout.
- Azure AI Foundry / Azure OpenAI calls use the `openai` Python package with
  `DefaultAzureCredential`.
- Azure AI Content Safety uses `azure-ai-contentsafety`.
- App settings are read from TOML with the standard-library `tomllib`.
- Tests use standard-library `unittest`.
- Azure resources are described with Bicep and helper shell scripts in
  `deployment/`.

### Project shape

- `src/foundry_ai_basics/main.py` runs the sample flow.
- `src/foundry_ai_basics/config.py` loads `settings.toml`.
- `src/foundry_ai_basics/clients.py` creates Azure/OpenAI clients.
- `src/foundry_ai_basics/display.py` prints output.
- `src/foundry_ai_basics/ai/` contains prompts, routing, and safety logic.

## Setup

- Non-secret app behavior settings live in `settings.toml`.
- Azure endpoint/deployment values are required environment variables.
- Do not commit secrets, tokens, or local-only settings.

## Test

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover
```
