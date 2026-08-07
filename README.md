# foundry-ai-basics

Small Azure AI Foundry practice app for AI-103 learning.

## Structure

- `main.py` runs the sample.
- `config.py` loads settings.
- `clients.py` creates Azure clients.
- `display.py` prints output.
- `ai/` contains prompts, routing, and safety logic.
- `deployment/` contains Azure deployment files.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
az login
```

Edit `settings.toml` with your Azure endpoints and deployment names.

## Run Tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover
```
