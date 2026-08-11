# Project Notes For AI Helpers

## Project Purpose

This is a small Azure AI Foundry practice app for AI-103 learning. It is meant
to be readable, beginner friendly, and easy to change while learning Azure AI
concepts.

Optimize for clarity over cleverness. Prefer small functions, explicit names,
standard-library tools, and simple control flow.

## Tech Stack

- Python 3.11+ package using the `src/` layout.
- Azure AI Foundry and Azure OpenAI calls use the `openai` Python package with
  `DefaultAzureCredential`.
- Azure AI Content Safety uses `azure-ai-contentsafety`.
- Azure AI Search is used for sample grounding/vector search.
- App settings are read from TOML with standard-library `tomllib`.
- Tests use standard-library `unittest`.
- Azure resources are described with Bicep and helper shell scripts in
  `deployment/`.

## Project Shape

- `src/foundry_ai_basics/main.py` runs the sample flow and should stay thin.
- `src/foundry_ai_basics/config.py` loads TOML settings and environment values
  into frozen dataclasses.
- `src/foundry_ai_basics/clients.py` creates Azure/OpenAI clients.
- `src/foundry_ai_basics/display.py` owns console output formatting.
- `src/foundry_ai_basics/open_telemetry.py` owns tracing/Application Insights
  helper code.
- `src/foundry_ai_basics/ai/` contains prompts, routing, safety, tools, MCP,
  and search logic.
- `tests/` contains focused `unittest` tests with fake clients/mocks instead of
  live Azure calls.

## Coding Style

- Keep modules small and responsibilities obvious.
- Add new behavior near the matching feature area. For example, routing changes
  belong in `ai/routing.py`; config changes belong in `config.py`.
- Prefer dataclasses for structured app configuration.
- Prefer plain functions unless shared state is really needed.
- Use type hints for public helpers and any non-obvious values.
- Keep comments short and useful. Do not explain code that is already clear.
- Avoid broad refactors while making a narrow learning change.
- Keep examples practical and easy to run from PowerShell.

## Configuration And Secrets

- Non-secret behavior settings belong in `settings.toml`.
- Azure endpoints, deployment names, API keys, connection strings, and local
  secrets belong in environment variables.
- Do not commit secrets, tokens, personal subscription IDs, or local-only
  credentials.
- When adding a required setting, update `AppConfig`, `load_config`, README
  setup notes, and tests together.
- Use clear errors for missing required settings or environment variables.

## Azure And AI Patterns

- Use `DefaultAzureCredential` for Azure authentication.
- Keep client creation centralized in `clients.py`.
- Keep prompts and prompt safety boundaries in `ai/prompts.py`.
- Keep moderation checks explicit and easy to inspect in `ai/safety.py`.
- Keep model routing behavior in `ai/routing.py`; preserve the simple SLM vs LLM
  routing idea unless the user asks for a larger redesign.
- Keep tool schemas and local sample tool implementations in `ai/tools.py`.
- Keep MCP-specific tool discovery/calling in `ai/mcp.py`.
- For grounding/search changes, keep Azure AI Search index details and sample
  documents in `ai/search.py`.

## Testing

Use `unittest` and avoid live Azure calls in tests. Prefer fake clients,
`unittest.mock.patch`, and captured stdout for behavior that prints.

Run tests with:

```powershell
$env:PYTHONPATH='src'; .\.venv\Scripts\python.exe -m unittest discover
```

When adding behavior:

- Add or update focused tests for pure logic, config parsing, routing decisions,
  search formatting, and tool handling.
- Mock network, Azure, OpenAI, MCP, and Content Safety calls.
- Keep tests readable for someone learning the project.

## Documentation

- Update `README.md` when setup steps, environment variables, commands, or the
  sample flow change.
- Keep docs short and concrete.
- Prefer examples that work on Windows PowerShell, because this repo is usually
  run from Windows.

## How To Work In This Repo

- First inspect the nearby code and follow its existing pattern.
- Make the smallest useful change that solves the request.
- Preserve beginner-friendly structure even if a more abstract design is
  possible.
- Do not introduce new dependencies unless they clearly simplify Azure/OpenAI
  integration or testing.
- Do not run deployment or cleanup scripts unless the user explicitly asks.
- Before finishing, explain what changed and mention any tests that were or were
  not run.
