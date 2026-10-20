"""Small, atomic preference updates shared by quick controls."""
import json
import os
from pathlib import Path
import tempfile

ORB_CHOICES = (
    ("neural_blue", "Rede azul pulsante"),
    ('android_particle', 'Esfera Android'),
    ('nebula', 'Brasa e fumaça'),
    ('particle', 'Partículas'),
)


def save_orb_choice(config_dir, style):
    if style not in dict(ORB_CHOICES):
        raise ValueError('Esfera desconhecida')
    directory = Path(config_dir)
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / 'ux.json'
    data = json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}
    if not isinstance(data, dict):
        raise ValueError('Configuração visual inválida')
    data['face'] = style
    data['orb_choice_saved'] = True
    fd, temp = tempfile.mkstemp(prefix='.ux-', suffix='.tmp', dir=directory)
    try:
        with os.fdopen(fd, 'w', encoding='utf-8') as handle:
            json.dump(data, handle, indent=2, ensure_ascii=False)
            handle.write('\n')
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)
