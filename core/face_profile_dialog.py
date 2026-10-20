"""Explicit enrollment and camera controls; matching runs outside the UI thread."""
import threading
from pathlib import Path
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import QDialog,QVBoxLayout,QHBoxLayout,QLabel,QLineEdit,QPushButton,QComboBox,QFileDialog,QCheckBox,QSpinBox
from core.face_profiles import FaceProfiles,FaceMatcher


class FaceProfileDialog(QDialog):
    result_ready=pyqtSignal(object,str)
    def __init__(self,config_dir,models,on_change,parent=None):
        super().__init__(parent,Qt.WindowType.Tool)
        self.store=FaceProfiles(config_dir);self.models=models;self.on_change=on_change
        self.stop=threading.Event();self.working=False;self.picture=None
        self.setWindowTitle('JARVIS — Foto e reconhecimento');self.resize(440,480)
        layout=QVBoxLayout(self)
        self.profiles=QComboBox();layout.addWidget(self.profiles)
        self.profiles.currentIndexChanged.connect(self.select)
        self.name=QLineEdit();self.name.setPlaceholderText('Nome do novo usuário');layout.addWidget(self.name)
        photo=QPushButton('Escolher foto');photo.clicked.connect(self.choose);layout.addWidget(photo)
        camera_photo=QPushButton('Tirar foto pela câmera');camera_photo.clicked.connect(self.capture);layout.addWidget(camera_photo)
        self.add=QPushButton('Cadastrar usuário');self.add.clicked.connect(self.enroll);layout.addWidget(self.add)
        remove=QPushButton('Excluir perfil selecionado');remove.clicked.connect(self.remove);layout.addWidget(remove)
        self.enabled=QCheckBox('Mostrar foto durante a conversa');layout.addWidget(self.enabled)
        self.size=QSpinBox();self.size.setRange(80,180);self.size.setPrefix('Tamanho: ');layout.addWidget(self.size)
        self.shape=QComboBox();self.shape.addItems(['circle','rounded']);layout.addWidget(self.shape)
        self.border=QLineEdit();self.border.setPlaceholderText('Cor da borda: #56c8ef');layout.addWidget(self.border)
        save=QPushButton('Salvar aparência');save.clicked.connect(self.save);layout.addWidget(save)
        self.recognize=QPushButton('Reconhecer pela câmera (10 s)');self.recognize.clicked.connect(self.verify);layout.addWidget(self.recognize)
        self.note=QLabel('A foto cadastrada não comprova identidade. A câmera abre somente ao clicar em reconhecer. Comparação local sem prova de presença; não substitui Windows Hello.');self.note.setWordWrap(True);layout.addWidget(self.note)
        self.result_ready.connect(self.result)
        self.reload()

    def reload(self):
        data=self.store.load();self.profiles.blockSignals(True);self.profiles.clear()
        for p in data['profiles']:self.profiles.addItem(p['name'],p['id'])
        self.profiles.setCurrentIndex(max(0,self.profiles.findData(data.get('active'))));self.profiles.blockSignals(False)
        self.enabled.setChecked(data.get('enabled',True));self.size.setValue(data.get('size',116))
        self.shape.setCurrentText(data.get('shape','circle'));self.border.setText(data.get('border','#56c8ef'))

    def select(self):
        data=self.store.load();data['active']=self.profiles.currentData();self.store.save(data);self.on_change(None)

    def choose(self):
        path,_=QFileDialog.getOpenFileName(self,'Foto do usuário','','Imagens (*.png *.jpg *.jpeg *.webp)')
        if path:self.picture=path;self.note.setText('Foto escolhida. Preencha o nome e clique em Cadastrar usuário.')

    def capture(self):
        if self.working:return
        self.working=True;self.stop.clear();self.note.setText('Abrindo câmera para tirar uma foto…')
        def work():
            camera=None
            try:
                import cv2
                import uuid
                camera=cv2.VideoCapture(0)
                if not camera.isOpened():raise ValueError('Câmera indisponível')
                frame=None
                for _ in range(8):
                    if self.stop.is_set():return
                    ok,frame=camera.read()
                    if not ok:raise ValueError('Câmera sem imagem')
                path=self.store.root/('capture-'+uuid.uuid4().hex+'.png')
                ok,data=cv2.imencode('.png',frame)
                if not ok:raise ValueError('Falha ao capturar foto')
                path.write_bytes(data.tobytes())
                self.result_ready.emit({'photo':str(path)},'Foto capturada. Informe o nome e cadastre o usuário.')
            except Exception:
                try:self.result_ready.emit(None,'Não foi possível capturar. Confira a câmera e as permissões.')
                except RuntimeError:pass
            finally:
                if camera is not None:camera.release()
        threading.Thread(target=work,daemon=True).start()

    def enroll(self):
        if not self.name.text().strip() or not self.picture:
            self.note.setText('Escolha uma foto e informe o nome.');return
        try:
            self.store.add(self.name.text(),self.picture);self.reload();self.on_change(None)
            self.note.setText('Perfil cadastrado. Reconhecimento ainda não realizado.')
        except Exception as exc:self.note.setText(str(exc))

    def remove(self):
        key=self.profiles.currentData()
        if key:self.store.remove(key);self.reload();self.on_change(None)

    def save(self):
        from PyQt6.QtGui import QColor
        if not QColor(self.border.text()).isValid():self.note.setText('Cor inválida. Use #56c8ef, por exemplo.');return
        data=self.store.load();data.update(enabled=self.enabled.isChecked(),size=self.size.value(),shape=self.shape.currentText(),border=self.border.text())
        self.store.save(data);self.on_change(None);self.note.setText('Aparência salva.')

    def verify(self):
        if self.working:return
        self.working=True;self.recognize.setEnabled(False);self.stop.clear()
        profiles=self.store.load()['profiles']
        self.note.setText('Olhe para a câmera. Comparando localmente…')
        def work():
            try:key=FaceMatcher(self.models).recognize_camera(profiles,self.stop);message='Rosto reconhecido.' if key else 'Rosto não reconhecido.'
            except Exception: key=None;message='Não foi possível reconhecer. Confira câmera, modelos e foto cadastrada.'
            try:self.result_ready.emit(key,message)
            except RuntimeError:pass
        threading.Thread(target=work,daemon=True).start()

    def result(self,key,message):
        self.working=False;self.recognize.setEnabled(True);self.note.setText(message)
        if self.stop.is_set():return
        if isinstance(key,dict):
            self.picture=key['photo'];return
        if key:
            data=self.store.load();data['active']=key;self.store.save(data);self.reload()
        self.on_change(key)

    def closeEvent(self,event):
        self.stop.set();super().closeEvent(event)
