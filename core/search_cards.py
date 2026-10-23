"""Parse existing search results into explicit, validated links."""
import re
from urllib.parse import urlsplit


def safe_url(value):
    try:
        parsed=urlsplit(value.strip())
        return value.strip() if parsed.scheme in ('https','http') and parsed.hostname and not parsed.username and not parsed.password else None
    except ValueError:return None


def search_cards(text):
    cards=[]
    for block in re.split(r'\n(?=\s*\d+\.\s)', '\n'+text):
        match=re.match(r'\s*\d+\.\s+([^\n]+)\n(.*)',block,re.S)
        if not match:continue
        title,body=match.groups()
        source=re.search(r'(?:Source|Fonte):\s*(https?://\S+)',body)
        if not source:
            source=re.search(r'^\s*(https?://\S+)\s*$',body,re.M)
        if not source:continue
        url=safe_url(source.group(1))
        if not url:continue
        image=re.search(r'^(?:Image|Imagem):\s*(\S+)',body,re.M)
        # Metadata is never rendered as rich text or treated as an executable URL.
        summary=body.replace(source.group(0),'')
        summary=re.sub(r'^\s*(?:Image|Imagem):[^\n]*','',summary,flags=re.M).strip()
        cards.append(dict(title=title.strip()[:180],summary=summary[:600],url=url,
                          domain=urlsplit(url).hostname,image=safe_url(image.group(1)) if image else None))
    return cards[:12]


def make_search_widget(text,parent=None):
    cards=search_cards(text)
    if not cards:return None
    from ui_components.briefing import BriefingDeck
    deck=BriefingDeck(parent)
    deck.set_content('PESQUISA · FONTES',text)
    return deck
