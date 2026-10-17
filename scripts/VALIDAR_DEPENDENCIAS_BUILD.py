from pathlib import Path
import re, sys

ROOT = Path(__file__).resolve().parent.parent
errors = []

for name in ("requirements.txt", "requirements-build.txt"):
    p = ROOT / name
    if not p.exists():
        errors.append(f"{name}: arquivo ausente")
        continue
    for i, line in enumerate(p.read_text(encoding="utf-8", errors="ignore").splitlines(), 1):
        if re.match(r"^\s*winsdk\b", line, flags=re.I):
            errors.append(f"{name}:{i}: winsdk NÃO pode estar nas dependências obrigatórias")

if sys.version_info >= (3, 13):
    errors.append(
        f"Python {sys.version_info.major}.{sys.version_info.minor} detectado. "
        "O build de teste deve usar Python 3.12 ou 3.11 para evitar pacotes sem wheel."
    )

if errors:
    print("\n[ERRO DE AMBIENTE]\n")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("[OK] Dependências obrigatórias limpas.")
print(f"[OK] Python compatível: {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")
print("[OK] winsdk está isolado como opcional.")
