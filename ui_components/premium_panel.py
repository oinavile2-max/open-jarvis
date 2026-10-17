"""Native modular overlay. Shares live state/audio/GPU frames with the main HUD."""
from __future__ import annotations
import datetime as dt
import math
import threading
import time
from PyQt6.QtCore import QPointF, QRectF, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QColor, QFont, QLinearGradient, QPainter, QPen, QRadialGradient
from PyQt6.QtWidgets import (QWidget,QLabel,QPushButton,QVBoxLayout,QHBoxLayout,
    QInputDialog,QColorDialog,QMenu,QMessageBox,QDialog,QCheckBox,QSlider,QComboBox)
from core.panel_settings import PanelSettings, CARDS
from core.panel_weather import condition

class WeatherScene(QWidget):
    def __init__(self,parent=None):
        super().__init__(parent);self.data=None;self.animate=True;self.t=0.
        self.setMinimumHeight(70)
        self.timer=QTimer(self);self.timer.timeout.connect(self.step);self.timer.start(50)
    def step(self):
        if self.isVisible() and self.animate:self.t+=.05;self.update()
    def paintEvent(self,event):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        if not self.data:return
        w,h=self.width(),self.height();day=self.data['day'];code=self.data['code']
        sky=QLinearGradient(0,0,0,h)
        sky.setColorAt(0,QColor('#173b59' if day else '#070f24'))
        sky.setColorAt(1,QColor('#496778' if day else '#20253e'))
        p.fillRect(self.rect(),sky)
        x,y=w*.74,h*.32
        glow=QRadialGradient(QPointF(x,y),h*.65)
        glow.setColorAt(0,QColor(255,207,126,125) if day else QColor(160,190,245,65))
        glow.setColorAt(1,QColor(0,0,0,0));p.setPen(Qt.PenStyle.NoPen);p.setBrush(glow)
        p.drawEllipse(QPointF(x,y),h*.65,h*.65)
        body=QRadialGradient(QPointF(x-h*.025,y-h*.025),h*.13)
        body.setColorAt(0,QColor('#fff6d8' if day else '#edf3ff'))
        body.setColorAt(1,QColor('#ffc66a' if day else '#8b9ec2'))
        p.setBrush(body);p.drawEllipse(QPointF(x,y),h*.13,h*.13)
        if not day:
            for i in range(24):
                xx=((i*71.7)%251)/251*w;yy=((i*39.1)%97)/97*h*.7
                p.setBrush(QColor(213,228,255,100+int(55*math.sin(self.t*.4+i))))
                p.drawEllipse(QPointF(xx,yy),.7,.7)
            # Shadow follows the lunar synodic phase, independently of weather.
            days=(dt.datetime.now(dt.timezone.utc)-dt.datetime(2000,1,6,18,14,tzinfo=dt.timezone.utc)).total_seconds()/86400
            phase=(days/29.530588853)%1
            p.setBrush(QColor('#17233d'))
            p.drawEllipse(QPointF(x+h*.19*math.cos(phase*math.tau),y),h*.125,h*.125)
        clouds=int(2+self.data['cloud']/17)
        for j in range(clouds):
            xx=((j*.211+self.t*.007*(1+j*.05))%1.5-.25)*w
            yy=h*(.47+.09*math.sin(j*2.3));size=h*(.22+.04*math.sin(j))
            for k in range(6):
                cx=xx+(k-2.5)*size*.35;cy=yy-math.sin(k*.7+j)*size*.24
                cloud=QRadialGradient(QPointF(cx-size*.15,cy-size*.3),size)
                a=190 if day else 135
                cloud.setColorAt(0,QColor(227 if day else 126,233 if day else 140,236 if day else 160,a))
                cloud.setColorAt(.53,QColor(117,134,151,int(a*.7)))
                cloud.setColorAt(1,QColor(60,75,96,0))
                p.setBrush(cloud);p.drawEllipse(QPointF(cx,cy),size,size*.65)
        rain=code in (51,53,55,56,57,61,63,65,66,67,80,81,82,95,96,99)
        snow=code in (71,73,75,77,85,86)
        if rain or snow:
            p.setPen(QPen(QColor(182,211,240,110),1.))
            for i in range(48):
                xx=((i*.618)%1)*w;yy=((i*.37+self.t*(.8 if rain else .12))%1)*h
                if rain:p.drawLine(QPointF(xx,yy),QPointF(xx-3,yy+10))
                else:p.drawEllipse(QPointF(xx+math.sin(self.t+i)*6,yy),1.6,1.6)
        if code in (95,96,99) and int(self.t*9)%107==0:
            p.fillRect(self.rect(),QColor(220,232,255,75))

class ModuleCard(QWidget):
    changed=pyqtSignal()
    def __init__(self,key,title,parent):
        super().__init__(parent);self.key=key;self.edit=False;self.drag=None
        self.setObjectName('moduleCard');self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground);self.setMinimumSize(190,130)
        self.layout_=QVBoxLayout(self);self.layout_.setContentsMargins(17,13,17,13);self.layout_.setSpacing(8)
        self.title=QLabel(title);self.title.setObjectName('moduleTitle');self.title.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.layout_.addWidget(self.title)
    def mousePressEvent(self,e):
        if self.edit and e.button()==Qt.MouseButton.LeftButton:
            self.drag=(e.globalPosition(),self.geometry(),e.position().x()>self.width()-24 and e.position().y()>self.height()-24)
            self.raise_();e.accept()
    def mouseMoveEvent(self,e):
        if self.drag:
            start,rect,resize=self.drag;delta=e.globalPosition()-start
            if resize:self.resize(max(190,rect.width()+int(delta.x())),max(130,rect.height()+int(delta.y())))
            else:self.move(max(0,min(self.parent().width()-self.width(),rect.x()+int(delta.x()))),
                           max(74,min(self.parent().height()-self.height(),rect.y()+int(delta.y()))))
    def mouseReleaseEvent(self,e):
        if self.drag:self.drag=None;self.changed.emit()
    def paintEvent(self,event):
        super().paintEvent(event)
        if self.edit:
            p=QPainter(self);p.setPen(QColor('#bd8f73'))
            for i in (0,5,10):p.drawLine(self.width()-6-i,self.height()-5,self.width()-5,self.height()-6-i)

class PremiumPanel(QWidget):
    weather_result=pyqtSignal(object)
    geocode_result=pyqtSignal(object)
    TITLES={'weather':'ATMOSFERA','clock':'TEMPO · CALENDÁRIO','system':'ESTAÇÃO',
            'home':'CASA CONECTADA','automation':'COMANDOS PESSOAIS'}
    def __init__(self,hud,send_command=None,home_config=None,parent=None,settings=None):
        super().__init__(parent,Qt.WindowType.Window|Qt.WindowType.FramelessWindowHint|Qt.WindowType.WindowStaysOnTopHint)
        self.hud=hud;self.send_command=send_command;self.home_config=home_config
        self.settings=settings or PanelSettings();self.cards={};self._busy=False
        self._drag=None;self._metrics_at=0.;self._last_weather=0.;self._editing=False
        self.setWindowTitle('JARVIS · Painel vivo');self.resize(1240,800);self.setMinimumSize(1000,680)
        self.top=QWidget(self);bar=QHBoxLayout(self.top);bar.setContentsMargins(24,12,24,12)
        logo=QLabel('J A R V I S');logo.setStyleSheet('font-size:22px;letter-spacing:5px;font-weight:600');bar.addWidget(logo)
        self.status=QLabel('PRESENÇA DIGITAL');bar.addWidget(self.status);bar.addStretch()
        for text,fn in [('Personalizar',self.customize),('Organizar',self.toggle_edit),('Recolher',self.hide)]:
            b=QPushButton(text);b.clicked.connect(fn);bar.addWidget(b)
        for key,title in self.TITLES.items():
            card=ModuleCard(key,title,self);card.changed.connect(self.save_layout);self.cards[key]=card
        self.weather_scene=WeatherScene();self.cards['weather'].layout_.addWidget(self.weather_scene,1)
        self.weather_value=QLabel('Escolha sua cidade');self.weather_value.setWordWrap(True)
        self.cards['weather'].layout_.addWidget(self.weather_value)
        self.city_button=QPushButton('Escolher cidade');self.city_button.clicked.connect(self.choose_city)
        self.cards['weather'].layout_.addWidget(self.city_button)
        self.clock=QLabel();self.clock.setStyleSheet('font-size:38px;font-weight:300')
        self.date=QLabel();self.cards['clock'].layout_.addWidget(self.clock);self.cards['clock'].layout_.addWidget(self.date)
        self.cards['clock'].layout_.addStretch()
        self.metrics=QLabel('Lendo métricas locais…');self.metrics.setWordWrap(True);self.metrics.setStyleSheet('font-size:16px;line-height:1.6')
        self.cards['system'].layout_.addWidget(self.metrics,1)
        self.home=QLabel('Nenhum dispositivo confirmado neste painel.\n\nConfigure a integração para conectar sua casa.');self.home.setWordWrap(True)
        self.cards['home'].layout_.addWidget(self.home,1)
        self.home_button=QPushButton('Configurar casa inteligente');self.home_button.clicked.connect(self.open_home)
        self.cards['home'].layout_.addWidget(self.home_button)
        self.command_row=QHBoxLayout();self.cards['automation'].layout_.addLayout(self.command_row)
        self.add_command=QPushButton('+ Adicionar comando');self.add_command.clicked.connect(self.new_command)
        self.cards['automation'].layout_.addWidget(self.add_command)
        self.rebuild_commands()
        self.weather_result.connect(self.weather_done);self.geocode_result.connect(self.geocode_done)
        self.timer=QTimer(self);self.timer.timeout.connect(self.tick);self.timer.start(33)
        self.apply_style();self.place_cards()
    def apply_style(self):
        a=self.settings.data['accent'];self.setWindowOpacity(self.settings.data['opacity'])
        self.setStyleSheet(f'''QWidget{{color:#e9e6e2;font-family:Segoe UI;background:transparent;}}
        QWidget#moduleCard{{background:rgba(17,20,28,232);border:1px solid #34313a;border-radius:18px;}}
        QLabel#moduleTitle{{color:{a};font-size:10px;font-weight:600;letter-spacing:2px;}}
        QPushButton{{background:#1b202b;border:1px solid #393a43;border-radius:9px;padding:8px 12px;font-size:11px;}}
        QPushButton:hover{{border-color:{a};background:#292b35;}}''')
        self.weather_scene.animate=self.settings.data['animations']
    def place_cards(self):
        self.top.setGeometry(0,0,self.width(),72)
        for key,card in self.cards.items():
            rect,visible=self.settings.card(key)
            card.setGeometry(int(rect[0]*self.width()),int(rect[1]*self.height()),int(rect[2]*self.width()),int(rect[3]*self.height()))
            card.setVisible(visible)
    def resizeEvent(self,e):self.place_cards();super().resizeEvent(e)
    def save_layout(self):
        for key,c in self.cards.items():
            self.settings.data['cards'][key]={'rect':[c.x()/self.width(),c.y()/self.height(),c.width()/self.width(),c.height()/self.height()], 'visible':not c.isHidden()}
        self.persist()
    def persist(self):
        try:self.settings.save()
        except OSError as e:QMessageBox.warning(self,'Personalização',f'Não foi possível salvar: {e}')
    def toggle_edit(self):
        self._editing=not self._editing
        for c in self.cards.values():c.edit=self._editing;c.update()
        self.status.setText('ARRASTE OS CARTÕES · CANTO INFERIOR REDIMENSIONA' if self._editing else 'PRESENÇA DIGITAL')
        if not self._editing:self.save_layout()
    def customize(self):
        d=QDialog(self);d.setWindowTitle('Personalizar painel');layout=QVBoxLayout(d)
        for key,c in self.cards.items():
            cb=QCheckBox(self.TITLES[key]);cb.setChecked(not c.isHidden());cb.toggled.connect(c.setVisible);layout.addWidget(cb)
        colour=QPushButton('Escolher cor de destaque');layout.addWidget(colour)
        def pick():
            c=QColorDialog.getColor(QColor(self.settings.data['accent']),d)
            if c.isValid():self.settings.data['accent']=c.name();self.apply_style()
        colour.clicked.connect(pick)
        layout.addWidget(QLabel('Opacidade'))
        opacity=QSlider(Qt.Orientation.Horizontal);opacity.setRange(60,100);opacity.setValue(int(self.settings.data['opacity']*100));layout.addWidget(opacity)
        def set_opacity(v):self.settings.data['opacity']=v/100;self.apply_style()
        opacity.valueChanged.connect(set_opacity)
        animations=QCheckBox('Animações do clima');animations.setChecked(self.settings.data['animations']);layout.addWidget(animations)
        def animate(v):self.settings.data['animations']=v;self.apply_style()
        animations.toggled.connect(animate)
        quality=QComboBox();quality.addItems(['economy','balanced','premium']);quality.setCurrentText(self.settings.data['quality']);layout.addWidget(QLabel('Qualidade da esfera · aplicada na próxima abertura'));layout.addWidget(quality)
        quality.currentTextChanged.connect(lambda v:self.settings.data.update(quality=v))
        auto=QCheckBox('Mostrar painel ao despertar em outro aplicativo');auto.setChecked(self.settings.data['auto_overlay']);auto.toggled.connect(lambda v:self.settings.data.update(auto_overlay=v));layout.addWidget(auto)
        reset=QPushButton('Restaurar posições');layout.addWidget(reset)
        def reset_layout():self.settings.data['cards']={};self.place_cards()
        reset.clicked.connect(reset_layout)
        done=QPushButton('Salvar');done.clicked.connect(d.accept);layout.addWidget(done)
        d.exec();self.save_layout()
    def choose_city(self):
        if self._busy:return
        text,ok=QInputDialog.getText(self,'Clima','Cidade:')
        if not ok or not text.strip():return
        self._busy=True;self.city_button.setEnabled(False);self.weather_value.setText('Procurando cidades…')
        def run():
            try:
                from core.panel_weather import geocode
                result=geocode(text)
            except Exception as e:result=e
            self.geocode_result.emit(result)
        threading.Thread(target=run,daemon=True).start()
    def geocode_done(self,result):
        self._busy=False;self.city_button.setEnabled(True)
        if isinstance(result,Exception):self.weather_value.setText('Não foi possível localizar a cidade.');return
        labels=[r['label'] for r in result]
        selected,ok=QInputDialog.getItem(self,'Confirmar cidade','Local:',labels,0,False)
        if not ok:self.weather_value.setText('Seleção cancelada');return
        choice=result[labels.index(selected)]
        self.settings.data.update(city=choice['label'],latitude=choice['latitude'],longitude=choice['longitude'])
        self.persist();self.refresh_weather()
    def refresh_weather(self):
        if self._busy:return
        data=self.settings.data
        if data['latitude'] is None or data['longitude'] is None:return
        self._busy=True;self._last_weather=time.monotonic();self.weather_value.setText('Atualizando condições…')
        def run():
            try:
                from core.panel_weather import fetch_weather
                result=fetch_weather(data['latitude'],data['longitude'])
            except Exception as e:result=e
            self.weather_result.emit(result)
        threading.Thread(target=run,daemon=True).start()
    def weather_done(self,result):
        self._busy=False
        if isinstance(result,Exception):
            self.weather_value.setText('Clima indisponível · verifique sua conexão');self.weather_scene.data=None;self.weather_scene.update();return
        self.weather_scene.data=result;self.weather_scene.update()
        self.weather_value.setText(f"{result['temperature']:.0f}°  ·  {condition(result['code'])}\n{self.settings.data['city']}\nSensação {result['feels']:.0f}° · vento {result['wind']:.0f} km/h\nAtualização: {result['time'].replace('T',' ')} · Open-Meteo")
    def rebuild_commands(self):
        while self.command_row.count():
            item=self.command_row.takeAt(0)
            if item.widget():item.widget().deleteLater()
        for c in self.settings.data['commands']:
            button=QPushButton(c['name'][:24]);button.clicked.connect(lambda checked=False,text=c['text']:self.run_command(text))
            button.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
            button.customContextMenuRequested.connect(lambda point,b=button,c=c:self.command_menu(b,c,point))
            self.command_row.addWidget(button)
        self.command_row.addStretch()
    def command_menu(self,button,command,point):
        menu=QMenu(self);remove=menu.addAction('Remover comando')
        if menu.exec(button.mapToGlobal(point))==remove:
            self.settings.data['commands'].remove(command);self.persist();self.rebuild_commands()
    def new_command(self):
        if len(self.settings.data['commands'])>=8:QMessageBox.information(self,'Comandos','Limite de oito comandos neste cartão.');return
        name,ok=QInputDialog.getText(self,'Novo comando','Nome do botão:')
        if not ok or not name.strip():return
        text,ok=QInputDialog.getText(self,'Novo comando','O que você quer pedir ao JARVIS?')
        if not ok or not text.strip():return
        self.settings.data['commands'].append({'name':name.strip()[:40],'text':text.strip()[:1000]})
        self.persist();self.rebuild_commands()
    def run_command(self,text):
        if self.send_command:
            self.status.setText('COMANDO ENVIADO AO JARVIS')
            threading.Thread(target=self.send_command,args=(text,),daemon=True).start()
        else:self.status.setText('MOTOR DE COMANDOS NÃO CONECTADO')
    def open_home(self):
        if self.home_config:self.home_config()
        else:QMessageBox.information(self,'Casa inteligente','Integração ainda não configurada.')
    def tick(self):
        if not self.isVisible():return
        now=dt.datetime.now();self.clock.setText(now.strftime('%H:%M'))
        self.date.setText(now.strftime('%d / %m / %Y')+'\n'+['Segunda-feira','Terça-feira','Quarta-feira','Quinta-feira','Sexta-feira','Sábado','Domingo'][now.weekday()])
        if time.monotonic()-self._metrics_at>2:
            self._metrics_at=time.monotonic()
            try:
                import psutil
                self.metrics.setText(f'CPU   {psutil.cpu_percent():.0f}%\n\nMEMÓRIA   {psutil.virtual_memory().percent:.0f}%')
            except ImportError:self.metrics.setText('Monitoramento indisponível')
        if time.monotonic()-self._last_weather>600:self.refresh_weather()
        self.update()
    def showEvent(self,e):
        self.hud._premium_panel_visible=True
        super().showEvent(e)
    def hideEvent(self,e):
        self.hud._premium_panel_visible=False
        super().hideEvent(e)
    def closeEvent(self,e):self.hide();e.ignore()
    def keyPressEvent(self,e):
        if e.key()==Qt.Key.Key_Escape:self.hide()
        else:super().keyPressEvent(e)
    def mousePressEvent(self,e):
        if e.position().y()<72:self._drag=e.globalPosition()-QPointF(self.pos())
    def mouseMoveEvent(self,e):
        if self._drag is not None:self.move((e.globalPosition()-self._drag).toPoint())
    def mouseReleaseEvent(self,e):self._drag=None
    def paintEvent(self,e):
        p=QPainter(self);p.setRenderHint(QPainter.RenderHint.Antialiasing)
        bg=QLinearGradient(0,0,self.width(),self.height());bg.setColorAt(0,QColor('#090d15'));bg.setColorAt(1,QColor('#111018'));p.fillRect(self.rect(),bg)
        w,h=self.width(),self.height();cx,cy=w*.5,h*.40;r=min(w*.195,h*.27)
        live=getattr(self.hud,'_live_ember',None)
        if live is not None and live.image is not None and not live.failed:
            p.drawImage(QRectF(cx-r,cy-r,r*2,r*2),live.image)
        else:
            p.setPen(QColor('#b3a29a'));p.drawText(QRectF(cx-r,cy-20,2*r,40),Qt.AlignmentFlag.AlignCenter,
                'GPU indisponível' if live and live.failed else 'Preparando volume de brasa…')
        state='SPEAKING' if self.hud.speaking else self.hud.state
        names={'SPEAKING':'RESPONDENDO','LISTENING':'OUVINDO','THINKING':'PENSANDO','PROCESSING':'PROCESSANDO','SLEEPING':'EM ESPERA','IDLE':'PRONTO PARA VOCÊ'}
        p.setPen(QColor(self.settings.data['accent']));p.setFont(QFont('Segoe UI',11))
        p.drawText(QRectF(cx-r,cy+r*.90,r*2,28),Qt.AlignmentFlag.AlignCenter,names.get(state,state))
        amplitude=max(0.,min(1.,self.hud._amp_disp));t=time.monotonic()
        p.setPen(QPen(QColor(self.settings.data['accent']),1.2))
        for i in range(65):
            x=cx+(i-32)*3.4;level=(.18+.82*abs(math.sin(i*.53+t*3)))*amplitude
            length=2.+level*25.*math.exp(-((i-32)/24.)**2)
            p.drawLine(QPointF(x,cy+r*1.12-length),QPointF(x,cy+r*1.12+length))
        caption=str(getattr(self.hud,'caption',''))[:160]
        p.setPen(QColor('#b6b1b0'));p.setFont(QFont('Segoe UI',10))
        p.drawText(QRectF(w*.30,h*.68,w*.40,h*.065),Qt.AlignmentFlag.AlignCenter|Qt.TextFlag.TextWordWrap,caption)
