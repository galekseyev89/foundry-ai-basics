# foundry-ai-basics

Small Azure AI Foundry practice app for AI-103 learning.

## Structure

- `main.py` runs the sample.
- `config.py` loads settings.
- `clients.py` creates Azure clients.
- `display.py` prints output.
- `redis.py` contains optional session-memory helpers for future caching.
- `ai/` contains prompts, routing, and safety logic.
- `deployment/` contains Azure deployment files.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
az login
```

## Deploy Azure Resources

Run deployment commands from the `deployment/` folder.

Use `foundry-ai-basics.sh` as a command reference:

- The provisioning commands create the resource group, deploy the Bicep file,
  and print the deployment outputs.
- Use the deployment outputs to set the environment variables below.
- The cleanup commands delete or purge Azure resources when you are finished,
  so you do not continue to incur cost.

## Environment Variables

Edit `settings.toml` for sample behavior, including the optional Redis session
memory TTL and message-history limits. Set Azure values with environment
variables:

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<your-foundry-resource>.services.ai.azure.com/openai/v1"
$env:CONTENT_SAFETY_ENDPOINT = "https://<your-content-safety-resource>.cognitiveservices.azure.com/"
$env:SEARCH_SERVICE_ENDPOINT = "https://<your-search-service>.search.windows.net"
$env:LLM_DEPLOYMENT_NAME = "<your-llm-deployment>"
$env:SLM_DEPLOYMENT_NAME = "<your-slm-deployment>"
$env:EMBEDDING_MODEL_DEPLOYMENT_NAME = "<your-embedding-deployment>"
$env:APPLICATIONINSIGHTS_CONNECTION_STRING = "<your-application-insights-connection-string>"
$env:MCP_SERVER_URL = "<your-mcp-server-url>"
$env:MCP_API_KEY = "<your-mcp-api-key>"
$env:REST_API_ENDPOINT = "<your-rest-api-endpoint>"
$env:REST_API_KEY = "<your-rest-api-key>"
$env:EXCHANGE_RATE_API_ENDPOINT = "<your-exchange-rate-api-endpoint>"
$env:EXCHANGE_RATE_API_KEY = "<your-exchange-rate-api-key>"
$env:REDIS_HOST_NAME = "<your-cache-name>.redis.cache.windows.net"
$env:REDIS_ACCESS_KEY = "<your-redis-access-key>"
$env:SESSION_ID = "local-learning-session"
```

The deployment output prints the Azure endpoint, model deployment, search, and
Application Insights values. Keep API keys and connection strings out of
`settings.toml` and source control.

Redis is optional. If `REDIS_HOST_NAME` and `REDIS_ACCESS_KEY` are not set, the
app uses the in-memory fallback in `redis.py`. `SESSION_ID` is optional; set it
when you want Redis to reload the same conversation in a later run.

## Test

```powershell
$env:PYTHONPATH='src'
python -m unittest discover
```

## Run

```powershell
$env:PYTHONPATH='src'
python -m foundry_ai_basics.main
```

When prompted, type the message you want to send to the model.
The app keeps the conversation history while it is running. Submit a blank
message to exit.
