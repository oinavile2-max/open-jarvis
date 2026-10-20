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
        if not source:continue
        url=safe_url(source.group(1))
        if not url:continue
        summary=re.sub(r'(?:Source|Fonte):\s*\S+','',body).strip()
        cards.append(dict(title=title.strip()[:180],summary=summary[:600],url=url,domain=urlsplit(url).hostname))
    return cards[:12]


def make_search_widget(text,parent=None):
    from PyQt6.QtCore import Qt,QUrl
    from PyQt6.QtGui import QDesktopServices
    from PyQt6.QtWidgets import QWidget,QVBoxLayout,QHBoxLayout,QLabel,QPushButton,QScrollArea,QFrame
    cards=search_cards(text)
    if not cards:return None
    scroll=QScrollArea(parent);scroll.setWidgetResizable(True);scroll.setMinimumHeight(220)
    scroll.setStyleSheet('QScrollArea{background:#0b111b;border:0;}')
    inner=QWidget();layout=QVBoxLayout(inner);layout.setContentsMargins(14,10,14,12);layout.setSpacing(10)
    for card in cards:
        frame=QFrame();frame.setObjectName('SearchResult')
        frame.setStyleSheet('QFrame#SearchResult{background:#141e2c;border:1px solid #284057;border-radius:12px;} QLabel{background:transparent;color:#e7eff9;border:0;font:14px "Segoe UI";} QPushButton{background:#173c57;color:#9bdeff;border:1px solid #296486;border-radius:7px;padding:8px 18px;}')
        box=QVBoxLayout(frame);box.setContentsMargins(16,12,16,12);box.setSpacing(7)
        title=QLabel(card['title']);title.setTextFormat(Qt.TextFormat.PlainText);title.setWordWrap(True);title.setStyleSheet('font:600 16px "Segoe UI";color:#edf6ff;');box.addWidget(title)
        summary=QLabel(card['summary']);summary.setTextFormat(Qt.TextFormat.PlainText);summary.setWordWrap(True);summary.setMaximumHeight(78);box.addWidget(summary)
        row=QHBoxLayout();domain=QLabel(card['domain']);domain.setStyleSheet('color:#85a4bd;font:12px "Segoe UI";');row.addWidget(domain);row.addStretch()
        button=QPushButton('Abrir fonte');button.clicked.connect(lambda _,url=card['url']:QDesktopServices.openUrl(QUrl(url)))
        row.addWidget(button);box.addLayout(row);layout.addWidget(frame)
    layout.addStretch();scroll.setWidget(inner)
    return scroll
