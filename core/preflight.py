"""Nonblocking-at-callsite checks; never opens microphone or calls an AI API."""
def check_environment(config_path):
    import json
    from pathlib import Path
    results = []
    try:
        import sounddevice as sd
        devices = sd.query_devices()
        for direction in ('input', 'output'):
            count = sum(d.get('max_' + direction + '_channels', 0) > 0 for d in devices)
            results.append(('ok' if count else 'erro', f'{direction}: {count} dispositivo(s) disponível(is)'))
    except Exception:
        results.append(('erro', 'Não foi possível consultar dispositivos de áudio.'))
    try:
        config = json.loads(Path(config_path).read_text(encoding='utf-8'))
        has_key = bool(config.get('gemini_api_key') or config.get('api_key'))
        results.append(('ok' if has_key else 'atenção', 'Chave Gemini cadastrada.' if has_key else 'Confira a chave Gemini nos ajustes.'))
    except Exception:
        results.append(('atenção', 'Configuração Gemini indisponível ou inválida.'))
    results.append(('info', 'Conexão e credenciais só são confirmadas após conectar ao Gemini.'))
    return results
