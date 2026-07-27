import os
from dataclasses import dataclass, field


@dataclass(frozen=True)
class IntentClassifierConfig:
    max_tokens: int
    temperature: float
    top_p: float


@dataclass(frozen=True)
class ModelConfig:
    max_past_messages: int
    max_tokens: int
    temperature: float
    top_p: float


@dataclass(frozen=True)
class AppConfig:
    azure_openai_endpoint: str
    llm_deployment_name: str
    slm_deployment_name: str
    content_safety_endpoint: str
    user_name: str
    user_role: str
    severity_threshold: int = 1
    safe_response: str = "I cannot generate a response to this request."
    max_system_tokens: int = 4000
    intent_classifier: IntentClassifierConfig = field(
        default_factory=lambda: IntentClassifierConfig(
            max_tokens=5,
            temperature=0,
            top_p=1.0,
        )
    )
    llm: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            max_past_messages=10,
            max_tokens=150,
            temperature=0.5,
            top_p=0.5,
        )
    )
    slm: ModelConfig = field(
        default_factory=lambda: ModelConfig(
            max_past_messages=5,
            max_tokens=100,
            temperature=0.25,
            top_p=0.25,
        )
    )
    session_state: str = (
        "awaiting_order_number - user asked about refund but no order number"
    )
    grounding_results: str | None = None


def load_config() -> AppConfig:
    return AppConfig(
        azure_openai_endpoint=_required_env("AZURE_OPENAI_ENDPOINT"),
        llm_deployment_name=_required_env("LLM_DEPLOYMENT_NAME"),
        slm_deployment_name=_required_env("SLM_DEPLOYMENT_NAME"),
        content_safety_endpoint=_required_env("CONTENT_SAFETY_ENDPOINT"),
        user_name=os.getenv("USER_NAME", "customer"),
        user_role=os.getenv("USER_ROLE", "customer"),
    )


def _required_env(name: str) -> str:
    value = os.getenv(name)
    
    if not value:
        raise ValueError(f"Missing required environment variable: {name}")
    
    return value
