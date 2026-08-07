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

## Deploy Azure Resources

Run deployment commands from the `deployment/` folder.

Use `foundry-ai-basics.sh` as a command reference:

- The provisioning commands create the resource group, deploy the Bicep file,
  and print the deployment outputs.
- Use the deployment outputs to set the environment variables below.
- The cleanup commands delete or purge Azure resources when you are finished,
  so you do not continue to incur cost.

## Environment Variables

Edit `settings.toml` for sample behavior. Set Azure values with environment
variables:

```powershell
$env:AZURE_OPENAI_ENDPOINT = "https://<your-foundry-resource>.services.ai.azure.com/openai/v1"
$env:CONTENT_SAFETY_ENDPOINT = "https://<your-content-safety-resource>.cognitiveservices.azure.com/"
$env:LLM_DEPLOYMENT_NAME = "<your-llm-deployment>"
$env:SLM_DEPLOYMENT_NAME = "<your-slm-deployment>"
```

## Run Tests

```powershell
$env:PYTHONPATH='src'
python -m unittest discover
```
