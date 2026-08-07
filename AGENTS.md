# Project Notes For AI Helpers

This is a small Azure AI Foundry practice app for AI-103 learning.

Keep changes simple and beginner friendly. Prefer clear functions, small modules,
and standard-library tools when possible.

Project shape:

- `src/foundry_ai_basics/main.py` runs the sample flow.
- `src/foundry_ai_basics/config.py` loads `settings.toml`.
- `src/foundry_ai_basics/clients.py` creates Azure/OpenAI clients.
- `src/foundry_ai_basics/display.py` prints output.
- `src/foundry_ai_basics/ai/` contains prompts, routing, and safety logic.

Configuration:

- Non-secret app settings live in `settings.toml`.
- Azure endpoint/deployment values may be overridden with environment variables.
- Do not commit secrets, tokens, or local-only settings.

Before finishing changes, run:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover
```
