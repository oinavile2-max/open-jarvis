"""Native briefing cockpit: immediate local cards, optional bounded article images."""
from __future__ import annotations

import datetime as dt
import ipaddress
from urllib.parse import urlsplit
import time
from collections import OrderedDict

from PyQt6.QtCore import Qt, QTimer, QUrl, QRectF, pyqtSignal
from PyQt6.QtGui import QDesktopServices, QImageReader, QPainter, QPainterPath, QPixmap
from PyQt6.QtNetwork import QNetworkAccessManager, QNetworkRequest, QNetworkReply, QHostInfo
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                            QTextEdit, QScrollArea, QFrame)
from core.search_cards import search_cards, safe_url
from ui_components.content_workspace import Reactor

STYLE = '''
QWidget {color:#dceef1;background:transparent;font-family:Segoe UI;}
QWidget#briefingWindow {background:#030b11;}
QFrame#briefingCard {background:rgba(5,19,28,245);border:1px solid #225464;border-radius:12px;}
QLabel#eyebrow {color:#66d6df;font-size:10px;letter-spacing:2px;}
QLabel#headline {color:#edfcff;font-size:21px;font-weight:600;}
QPushButton {background:#0a202b;color:#a9eaf1;border:1px solid #24505f;border-radius:7px;padding:8px 12px;}
QPushButton:hover,QPushButton:checked {background:#123b48;border-color:#69e9ed;}
QPushButton:disabled {color:#59727b;border-color:#172f39;}
QTextEdit {background:transparent;border:0;color:#c2d7df;font-size:14px;}
QScrollArea {background:transparent;border:0;}
'''


def resolve_public_image(url,callback):
    """Resolve off the GUI thread; automatic images must not target local networks."""
    host=urlsplit(url).hostname or ''
    try:
        callback(ipaddress.ip_address(host).is_global)
        return None
    except ValueError:
        pass
    if '.' not in host or host.rstrip('.').endswith(('.local','.localhost','.internal')):
        callback(False)
        return None
    def resolved(info):
        addresses=info.addresses()
        allowed=bool(addresses) and all(ipaddress.ip_address(a.toString()).is_global for a in addresses)
        callback(allowed)
    return QHostInfo.lookupHost(host,resolved)


class BriefingDeck(QWidget):
    """Selected detail and horizontal thumbnails; selection never waits on the network."""
    presentation_changed=pyqtSignal()
    MAX_IMAGE_BYTES = 4 * 1024 * 1024

    def __init__(self, parent=None):
        super().__init__(parent)
        self.cards=[];self.index=-1;self.selected_url=None
        self._reply=None;self._buffer=bytearray();self._image_url=None
        self._generation=0;self._lookup_id=None;self._resolving=False
        self.deadline=QTimer(self);self.deadline.setSingleShot(True);self.deadline.timeout.connect(self._image_timeout)
        self._cache=OrderedDict();self._failed=set();self._buttons=[]
        self.network=QNetworkAccessManager(self)
        self.setStyleSheet(STYLE);self.setMinimumHeight(300)
        layout=QVBoxLayout(self);layout.setContentsMargins(0,0,0,0);layout.setSpacing(10)
        frame=QFrame();frame.setObjectName('briefingCard');layout.addWidget(frame,1)
        box=QVBoxLayout(frame);box.setContentsMargins(22,16,22,16)
        row=QHBoxLayout();self.category=QLabel('JARVIS · BRIEFING');self.category.setTextFormat(Qt.TextFormat.PlainText);self.category.setObjectName('eyebrow');row.addWidget(self.category)
        row.addStretch();self.counter=QLabel();row.addWidget(self.counter);box.addLayout(row)
        self.image=QLabel();self.image.setAlignment(Qt.AlignmentFlag.AlignCenter);self.image.setFixedHeight(170);self.image.hide();box.addWidget(self.image)
        self.title=QLabel('Seu briefing aparece aqui');self.title.setTextFormat(Qt.TextFormat.PlainText)
        self.title.setObjectName('headline');self.title.setWordWrap(True);box.addWidget(self.title)
        self.summary=QTextEdit();self.summary.setReadOnly(True);self.summary.setMinimumHeight(65);box.addWidget(self.summary,1)
        foot=QHBoxLayout();self.domain=QLabel();foot.addWidget(self.domain,1)
        self.source=QPushButton('Abrir fonte');self.source.setEnabled(False);self.source.clicked.connect(self.open_source);foot.addWidget(self.source);box.addLayout(foot)
        self.strip=QScrollArea();self.strip.setWidgetResizable(True);self.strip.setFixedHeight(100)
        self.strip.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        layout.addWidget(self.strip)
        nav=QHBoxLayout();previous=QPushButton('‹ Anterior');previous.clicked.connect(lambda:self.select(self.index-1));nav.addWidget(previous)
        nav.addStretch();following=QPushButton('Próximo ›');following.clicked.connect(lambda:self.select(self.index+1));nav.addWidget(following);layout.addLayout(nav)

    def set_content(self, category, text):
        self._cancel_image();self._failed.clear()
        self.cards=search_cards(str(text))
        if not self.cards:
            self.cards=[dict(title=str(category)[:180],summary=str(text)[:24000],url=None,domain='Resposta do JARVIS · sem fonte vinculada',image=None)]
        self.category.setText(str(category).upper()[:70])
        old=self.strip.takeWidget()
        if old:old.deleteLater()
        inner=QWidget();row=QHBoxLayout(inner);row.setContentsMargins(0,0,0,0);row.setSpacing(8);self._buttons=[]
        for index,card in enumerate(self.cards):
            button=QPushButton(f"{index+1:02d} · {card['title'][:65]}\n{card['domain'] or ''}")
            button.setFixedWidth(220);button.setMinimumHeight(70);button.setCheckable(True)
            button.clicked.connect(lambda checked=False,i=index:self.select(i));row.addWidget(button);self._buttons.append(button)
        row.addStretch();self.strip.setWidget(inner);self.select(0)

    def select(self, index):
        if not self.cards:return
        self._cancel_image();self.index=index%len(self.cards);card=self.cards[self.index]
        self.selected_url=safe_url(card['url'] or '')
        self.title.setText(card['title']);self.summary.setPlainText(card['summary'])
        self.summary.verticalScrollBar().setValue(0)
        self.domain.setText(card['domain'] or '');self.domain.setTextFormat(Qt.TextFormat.PlainText)
        self.source.setEnabled(bool(self.selected_url));self.counter.setText(f'{self.index+1:02d} / {len(self.cards):02d}')
        for i,button in enumerate(self._buttons):button.setChecked(i==self.index)
        self.strip.ensureWidgetVisible(self._buttons[self.index])
        self.image.clear();self.image.hide();self._image_url=card.get('image');self.presentation_changed.emit()
        if self.isVisible():self._load_image()

    def open_source(self):
        if self.selected_url:QDesktopServices.openUrl(QUrl(self.selected_url))

    def _load_image(self):
        url=safe_url(self._image_url or '')
        if not url or url in self._failed or self._reply or self._resolving:return
        if url in self._cache:self._show_image(self._cache[url]);return
        self._resolving=True;generation=self._generation;self.deadline.start(7000)
        def ready(allowed):
            from PyQt6 import sip
            if sip.isdeleted(self) or generation!=self._generation:return
            self._resolving=False;self._lookup_id=None
            if not allowed:
                self.deadline.stop();self._failed.add(url);return
            request=QNetworkRequest(QUrl(url));request.setTransferTimeout(7000)
            request.setAttribute(QNetworkRequest.Attribute.RedirectPolicyAttribute,QNetworkRequest.RedirectPolicy.ManualRedirectPolicy)
            self._buffer=bytearray();reply=self.network.get(request);self._reply=reply
            reply.readyRead.connect(lambda:self._read_image(reply))
            reply.finished.connect(lambda:self._image_finished(reply,url))
        self._lookup_id=resolve_public_image(url,ready)

    def _image_timeout(self):
        if self._image_url:self._failed.add(self._image_url)
        self._cancel_image()

    def _read_image(self,reply):
        if reply is not self._reply:return
        if reply.bytesAvailable()+len(self._buffer)>self.MAX_IMAGE_BYTES:
            self._failed.add(self._image_url);reply.abort();return
        self._buffer.extend(bytes(reply.readAll()))

    def _image_finished(self,reply,url):
        if reply is not self._reply:reply.deleteLater();return
        self._read_image(reply)
        data=bytes(self._buffer);self._reply=None;self.deadline.stop();reply.deleteLater()
        if reply.error()!=QNetworkReply.NetworkError.NoError or not data or len(data)>self.MAX_IMAGE_BYTES:
            self._failed.add(url);return
        # Check dimensions before decoding to bound expanded memory as well as transfer size.
        from PyQt6.QtCore import QBuffer, QByteArray, QIODevice
        buffer=QBuffer();buffer.setData(QByteArray(data));buffer.open(QIODevice.OpenModeFlag.ReadOnly)
        reader=QImageReader(buffer);size=reader.size()
        if not size.isValid() or size.width()*size.height()>16_000_000:
            self._failed.add(url);return
        pix=QPixmap.fromImage(reader.read())
        if pix.isNull():self._failed.add(url);return
        pix=pix.scaled(1000,500,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation)
        self._cache[url]=pix
        while len(self._cache)>12:self._cache.popitem(last=False)
        if url==self._image_url:self._show_image(pix)

    def _show_image(self,pix):
        self.image.setPixmap(pix.scaled(max(1,self.width()-48),170,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation));self.image.show();self.presentation_changed.emit()

    def _cancel_image(self):
        self.deadline.stop();self._generation+=1;self._resolving=False
        if self._lookup_id is not None:QHostInfo.abortHostLookup(self._lookup_id);self._lookup_id=None
        reply=self._reply;self._reply=None;self._buffer=bytearray()
        if reply:reply.abort()

    def showEvent(self,event):
        super().showEvent(event);self._load_image()

    def hideEvent(self,event):
        self._cancel_image();super().hideEvent(event)


class HaloStage(QWidget):
    def __init__(self,hud,parent=None):
        super().__init__(parent)
        self.reactor=Reactor(lambda:('SPEAKING' if getattr(hud,'speaking',False) else getattr(hud,'state','IDLE'),getattr(hud,'_amp_disp',0.)),self,show_label=False)
        self.reactor.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.deck=BriefingDeck(self)
        self.deck.presentation_changed.connect(self.place_deck)
        self.setMinimumHeight(420)

    def place_deck(self):
        width=max(500,min(700,self.width()-230))
        height=min(self.height()-32,530 if not self.deck.image.isHidden() else 370)
        self.deck.setGeometry((self.width()-width)//2,(self.height()-height)//2,width,height)

    def resizeEvent(self,event):
        self.reactor.setGeometry(0,0,self.width(),self.height())
        self.place_deck()
        super().resizeEvent(event)


class BriefingWindow(QWidget):
    """Video-inspired cockpit bound to existing HUD state, photo and response content."""
    def __init__(self,hud,send_command=None,weather=None,profiles=None,settings=None,parent=None):
        super().__init__(parent,Qt.WindowType.Window)
        self.hud=hud;self.send_command=send_command;self.setObjectName('briefingWindow')
        self.setWindowTitle('JARVIS · Central de briefing');self.resize(1180,850);self.setMinimumSize(900,700)
        self.setStyleSheet(STYLE);layout=QVBoxLayout(self);layout.setContentsMargins(30,20,30,20)
        bar=QHBoxLayout();logo=QLabel('●  J.A.R.V.I.S.  /  CENTRAL DE BRIEFING');logo.setObjectName('eyebrow');bar.addWidget(logo)
        self.clock=QLabel();bar.addStretch();bar.addWidget(self.clock)
        for text,callback in [('Clima',weather),('Perfil',profiles),('Ajustes',settings),('Recolher',self.hide)]:
            button=QPushButton(text);button.setEnabled(callback is not None)
            if callback:button.clicked.connect(callback)
            bar.addWidget(button)
        layout.addLayout(bar)
        stage=QHBoxLayout()
        identity_box=QVBoxLayout();self.photo=QLabel();self.photo.setFixedSize(84,84);self.identity=QLabel();self.identity.setTextFormat(Qt.TextFormat.PlainText)
        identity_box.addWidget(self.photo);identity_box.addWidget(self.identity);stage.addLayout(identity_box)
        self.caption=QLabel('Peça notícias, um resumo ou faça uma pesquisa.');self.caption.setTextFormat(Qt.TextFormat.PlainText);self.caption.setWordWrap(True);stage.addWidget(self.caption,1)
        layout.addLayout(stage)
        self.stage=HaloStage(hud);self.reactor=self.stage.reactor;self.deck=self.stage.deck;layout.addWidget(self.stage,1)
        self.deck.set_content('PRONTO PARA VOCÊ','Peça notícias ou uma pesquisa ao JARVIS. Os resultados com fontes aparecem em cartões selecionáveis. Nenhuma notícia de demonstração é carregada.')
        actions=QHBoxLayout()
        for title,prompt in [('Notícias','Pesquise as principais notícias de hoje e mostre os resultados com fontes.'),('Tecnologia','Pesquise notícias de tecnologia e inteligência artificial de hoje com fontes.'),('Meu dia','Resuma meus compromissos e tarefas de hoje usando somente os dados disponíveis.')]:
            button=QPushButton(title);button.setEnabled(send_command is not None)
            button.clicked.connect(lambda checked=False,p=prompt:self.command(p));actions.addWidget(button)
        self.state=QLabel();actions.addStretch();actions.addWidget(self.state);layout.addLayout(actions)
        self.timer=QTimer(self);self.timer.setInterval(100);self.timer.timeout.connect(self.sync)
        self._last_caption=None

    def command(self,text):
        if self.send_command:
            import threading
            threading.Thread(target=self.send_command,args=(text,),daemon=True).start()
            self.caption.setText('Pedido enviado ao JARVIS…')

    def set_content(self,title,text):
        self.deck.set_content(title,text)

    def sync(self):
        self.clock.setText(dt.datetime.now().strftime('%d/%m  ·  %H:%M'))
        state='SPEAKING' if getattr(self.hud,'speaking',False) else getattr(self.hud,'state','IDLE')
        self.state.setText({'SPEAKING':'RESPONDENDO','LISTENING':'OUVINDO','THINKING':'PENSANDO','SLEEPING':'EM ESPERA','IDLE':'PRONTO'}.get(state,state))
        caption=str(getattr(self.hud,'caption',''))
        if caption and caption!=self._last_caption:self.caption.setText(caption[:500]);self._last_caption=caption
        profile=getattr(self.hud,'_profile_data',None)
        visible=bool(profile and getattr(self.hud,'_profile_opacity',0.)>.05 and state!='SLEEPING')
        self.photo.setVisible(visible);self.identity.setVisible(visible)
        if visible:
            # Reuse the registration and recognition result; displaying a photo grants no identity claim.
            self.identity.setText(profile.get('name','')[:60]+('\nRosto reconhecido' if time.monotonic()<getattr(self.hud,'_profile_verified_until',0.) else '\nFoto cadastrada'))
            original=getattr(self.hud,'_profile_pixmap',QPixmap())
            pix=QPixmap(84,84);pix.fill(Qt.GlobalColor.transparent)
            painter=QPainter(pix);painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            path=QPainterPath();path.addEllipse(QRectF(1,1,82,82));painter.setClipPath(path)
            if not original.isNull():
                scaled=original.scaled(84,84,Qt.AspectRatioMode.KeepAspectRatioByExpanding,Qt.TransformationMode.SmoothTransformation)
                painter.drawPixmap((84-scaled.width())//2,(84-scaled.height())//2,scaled)
            painter.end();self.photo.setPixmap(pix)

    def showEvent(self,event):
        self.sync();self.timer.start();super().showEvent(event)

    def hideEvent(self,event):
        self.timer.stop();super().hideEvent(event)

    def closeEvent(self,event):
        self.hide();event.ignore()
