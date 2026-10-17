"""Small local setup helper for the optional Claude reasoning backend."""
from __future__ import annotations

import getpass
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CFG = ROOT / "config" / "api_keys.json"


def main() -> None:
    CFG.parent.mkdir(parents=True, exist_ok=True)
    try:
        data = json.loads(CFG.read_text(encoding="utf-8")) if CFG.exists() else {}
        if not isinstance(data, dict):
            data = {}
    except Exception:
        data = {}

    print("JARVIS - configuração opcional do Claude")
    print("A chave fica somente no arquivo local config/api_keys.json.")
    key = getpass.getpass("Anthropic API key (não aparece na tela): ").strip()
    if not key:
        print("Nenhuma chave informada. Nada foi alterado.")
        return

    model = input("Modelo [claude-sonnet-4-5]: ").strip() or "claude-sonnet-4-5"
    max_tokens_raw = input("Máximo de tokens por resposta [1200]: ").strip() or "1200"
    try:
        max_tokens = max(128, min(4096, int(max_tokens_raw)))
    except ValueError:
        max_tokens = 1200

    data["anthropic_api_key"] = key
    data["anthropic_model"] = model
    data["anthropic_max_tokens"] = max_tokens
    CFG.write_text(json.dumps(data, indent=4), encoding="utf-8")
    print("Claude configurado. A chave não foi exibida.")


if __name__ == "__main__":
    main()
