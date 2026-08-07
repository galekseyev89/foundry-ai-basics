import os
import tomllib
from dataclasses import dataclass
from pathlib import Path
from typing import Any


DEFAULT_CONFIG_PATH = Path("settings.toml")


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
class RoutedModelConfig:
    deployment_name: str
    model_type: str
    max_past_messages: int
    max_tokens: int
    temperature: float
    top_p: float


@dataclass(frozen=True)
class RoutingConfig:
    intent_classifier: IntentClassifierConfig
    llm: RoutedModelConfig
    slm: RoutedModelConfig


@dataclass(frozen=True)
class AppConfig:
    azure_openai_endpoint: str
    llm_deployment_name: str
    slm_deployment_name: str
    content_safety_endpoint: str
    user_name: str
    user_role: str
    intent_classifier: IntentClassifierConfig
    llm: ModelConfig
    slm: ModelConfig
    severity_threshold: int
    safe_response: str
    max_system_tokens: int
    session_state: str | None
    grounding_results: str | None = None

    @property
    def routing(self) -> RoutingConfig:
        return RoutingConfig(
            intent_classifier=self.intent_classifier,
            llm=RoutedModelConfig(
                deployment_name=self.llm_deployment_name,
                model_type="LLM",
                max_past_messages=self.llm.max_past_messages,
                max_tokens=self.llm.max_tokens,
                temperature=self.llm.temperature,
                top_p=self.llm.top_p,
            ),
            slm=RoutedModelConfig(
                deployment_name=self.slm_deployment_name,
                model_type="SLM",
                max_past_messages=self.slm.max_past_messages,
                max_tokens=self.slm.max_tokens,
                temperature=self.slm.temperature,
                top_p=self.slm.top_p,
            ),
        )


def load_config(config_path: str | Path | None = None) -> AppConfig:
    settings = _load_settings(config_path)

    return AppConfig(
        azure_openai_endpoint=_env_or_config_setting(
            settings,
            "AZURE_OPENAI_ENDPOINT",
            ["azure", "openai_endpoint"],
            required=True,
        ),
        llm_deployment_name=_env_or_config_setting(
            settings,
            "LLM_DEPLOYMENT_NAME",
            ["azure", "llm_deployment_name"],
            required=True,
        ),
        slm_deployment_name=_env_or_config_setting(
            settings,
            "SLM_DEPLOYMENT_NAME",
            ["azure", "slm_deployment_name"],
            required=True,
        ),
        content_safety_endpoint=_env_or_config_setting(
            settings,
            "CONTENT_SAFETY_ENDPOINT",
            ["azure", "content_safety_endpoint"],
            required=True,
        ),
        user_name=_required_config_setting(settings, ["user", "name"]),
        user_role=_required_config_setting(settings, ["user", "role"]),
        severity_threshold=_required_int_setting(
            settings,
            ["safety", "severity_threshold"],
        ),
        safe_response=_required_config_setting(settings, ["safety", "safe_response"]),
        max_system_tokens=_required_int_setting(
            settings,
            ["prompt", "max_system_tokens"],
        ),
        session_state=_optional_config_setting(settings, ["prompt", "session_state"]),
        grounding_results=_optional_config_setting(
            settings,
            ["prompt", "grounding_results"],
        ),
        intent_classifier=IntentClassifierConfig(
            max_tokens=_required_int_setting(
                settings, ["routing", "intent_classifier", "max_tokens"]
            ),
            temperature=_required_float_setting(
                settings, ["routing", "intent_classifier", "temperature"]
            ),
            top_p=_required_float_setting(
                settings, ["routing", "intent_classifier", "top_p"]
            ),
        ),
        llm=ModelConfig(
            max_past_messages=_required_int_setting(
                settings, ["routing", "llm", "max_past_messages"]
            ),
            max_tokens=_required_int_setting(
                settings,
                ["routing", "llm", "max_tokens"],
            ),
            temperature=_required_float_setting(
                settings, ["routing", "llm", "temperature"]
            ),
            top_p=_required_float_setting(settings, ["routing", "llm", "top_p"]),
        ),
        slm=ModelConfig(
            max_past_messages=_required_int_setting(
                settings, ["routing", "slm", "max_past_messages"]
            ),
            max_tokens=_required_int_setting(
                settings,
                ["routing", "slm", "max_tokens"],
            ),
            temperature=_required_float_setting(
                settings, ["routing", "slm", "temperature"]
            ),
            top_p=_required_float_setting(settings, ["routing", "slm", "top_p"]),
        ),
    )


def _load_settings(config_path: str | Path | None) -> dict[str, Any]:
    path = Path(config_path or os.getenv("APP_CONFIG_PATH") or DEFAULT_CONFIG_PATH)

    if not path.exists():
        return {}

    with path.open("rb") as config_file:
        return tomllib.load(config_file)


def _env_or_config_setting(
    settings: dict[str, Any],
    env_name: str,
    path: list[str],
    default: Any = None,
    required: bool = False,
) -> Any:
    env_value = os.getenv(env_name)
    if env_value is not None:
        return env_value

    value = _nested_value(settings, path, default)
    if required and value in (None, ""):
        joined_path = ".".join(path)
        raise ValueError(
            f"Missing required setting: {joined_path} or environment variable {env_name}"
        )

    return value


def _optional_config_setting(settings: dict[str, Any], path: list[str]) -> Any:
    return _nested_value(settings, path, None)


def _required_config_setting(settings: dict[str, Any], path: list[str]) -> Any:
    value = _nested_value(settings, path, None)
    if value in (None, ""):
        joined_path = ".".join(path)
        raise ValueError(f"Missing required setting: {joined_path}")

    return value


def _required_int_setting(settings: dict[str, Any], path: list[str]) -> int:
    return int(_required_config_setting(settings, path))


def _required_float_setting(settings: dict[str, Any], path: list[str]) -> float:
    return float(_required_config_setting(settings, path))


def _nested_value(settings: dict[str, Any], path: list[str], default: Any) -> Any:
    value: Any = settings
    for key in path:
        if not isinstance(value, dict) or key not in value:
            return default
        value = value[key]

    return value
