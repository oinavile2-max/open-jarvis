"""Provider-aware readiness; Claude typed commands do not require Gemini."""


def startup_ready(config: dict) -> bool:
    if config.get('brain_provider') == 'claude_code':
        return True
    return bool(config.get('gemini_api_key')) and bool(config.get('os_system'))
