from azure.ai.contentsafety import ContentSafetyClient
from azure.ai.contentsafety.models import AnalyzeTextOptions


def is_text_safe(
    content_safety_client: ContentSafetyClient,
    text_to_check: str,
    severity_threshold: int,
) -> bool:
    analysis_request = AnalyzeTextOptions(text=text_to_check)
    analysis_result = content_safety_client.analyze_text(analysis_request)

    categories_result = _get_categories_analysis(analysis_result)

    severities = {
        _get_value(category, "category"): _get_value(category, "severity")
        for category in categories_result
    }

    checks = [
        ("Hate", "HATE"),
        ("Sexual", "SEXUAL"),
        ("Violence", "VIOLENCE"),
        ("SelfHarm", "SELF_HARM"),
    ]

    for category, label in checks:
        severity = severities.get(category, 0)
        if severity > severity_threshold:
            print(f"Blocked: {label} (severity {severity})")
            return False

    return True


def _get_categories_analysis(analysis_result):
    if isinstance(analysis_result, dict):
        return analysis_result["categoriesAnalysis"]

    return analysis_result.categories_analysis


def _get_value(item, name: str):
    if isinstance(item, dict):
        return item[name]

    return getattr(item, name)
