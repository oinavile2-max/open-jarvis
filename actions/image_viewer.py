"""Display a local photo in a JARVIS smoked glass card instead of browser."""
from pathlib import Path


def image_viewer(parameters=None, player=None, **_kwargs):
    raw = str((parameters or {}).get('source') or '').strip().strip('"')
    if not raw:
        return 'Qual imagem devo abrir?'
    path = Path(raw).expanduser()
    if not path.is_file() or path.suffix.lower() not in ('.jpg','.jpeg','.png','.bmp','.webp'):
        return 'Imagem local não encontrada. Envie um caminho de imagem válido.'
    if path.stat().st_size > 30_000_000:
        return 'Essa imagem é grande demais para o cartão.'
    if player is None or not hasattr(player, 'show_image'):
        return 'O visor de imagens não está disponível nessa instalação.'
    player.show_image(str(path.resolve()), path.name)
    return 'Abri a imagem no cartão do JARVIS.'

TOOL = {
 'name':'image_viewer',
 'description':'Abre fotos e imagens locais (PNG, JPEG, WEBP e BMP) nos cards do JARVIS, sem navegador.',
 'parameters':{'type':'OBJECT','properties':{'source':{'type':'STRING','description':'Caminho local da imagem'}},'required':['source']},
 'handler':image_viewer,
}
