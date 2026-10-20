"""Local photo profiles and opt-in camera comparison. Never authenticates OS actions."""
import json
import time
import uuid
from pathlib import Path


class FaceProfiles:
    def __init__(self, config_dir):
        self.root=Path(config_dir)/'face_profiles'
        self.root.mkdir(parents=True,exist_ok=True)
        self.path=self.root/'profiles.json'

    def load(self):
        if not self.path.exists(): return {'active':None,'profiles':[],'enabled':True,'size':116,'shape':'circle','border':'#56c8ef'}
        return json.loads(self.path.read_text(encoding='utf-8'))

    def save(self,data):
        temp=self.path.with_suffix('.tmp')
        temp.write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
        temp.replace(self.path)

    def add(self,name,picture):
        from PyQt6.QtGui import QImage
        image=QImage(str(picture))
        if image.isNull(): raise ValueError('Foto inválida')
        key=uuid.uuid4().hex
        target=self.root/(key+'.png')
        from PyQt6.QtCore import Qt
        if not image.scaled(640,640,Qt.AspectRatioMode.KeepAspectRatio,Qt.TransformationMode.SmoothTransformation).save(str(target)):
            raise ValueError('Não foi possível salvar a foto')
        data=self.load();data['profiles'].append({'id':key,'name':name.strip()[:60],'photo':str(target)})
        data['active']=key;self.save(data)
        return key

    def remove(self,key):
        data=self.load()
        data['profiles']=[p for p in data['profiles'] if p['id']!=key]
        if data.get('active')==key: data['active']=None
        self.save(data)
        path=self.root/(key+'.png')
        if path.exists(): path.unlink()


class FaceMatcher:
    def __init__(self,models):
        import cv2
        self.cv=cv2
        self.detector=cv2.FaceDetectorYN.create(str(Path(models)/'yunet.onnx'),'',(320,320),.9,.3,500)
        self.recognizer=cv2.FaceRecognizerSF.create(str(Path(models)/'sface.onnx'),'')

    def feature(self,image):
        if image is None: raise ValueError('Imagem indisponível')
        h,w=image.shape[:2]
        scale=min(1.,640/max(h,w))
        if scale<1: image=self.cv.resize(image,(int(w*scale),int(h*scale)))
        self.detector.setInputSize((image.shape[1],image.shape[0]))
        _,faces=self.detector.detect(image)
        if faces is None or len(faces)!=1: raise ValueError('Mostre somente um rosto nítido à câmera')
        if min(faces[0][2:4])<60: raise ValueError('Aproxime o rosto da câmera')
        aligned=self.recognizer.alignCrop(image,faces[0])
        return self.recognizer.feature(aligned).copy()

    def recognize_camera(self,profiles,stop):
        import numpy as np
        refs=[]
        for p in profiles:
            try:
                image=self.cv.imdecode(np.fromfile(p['photo'],dtype=np.uint8),self.cv.IMREAD_COLOR)
                refs.append((p['id'],self.feature(image)))
            except ValueError: pass
        if not refs: raise ValueError('Cadastre uma foto com um único rosto nítido')
        camera=self.cv.VideoCapture(0)
        try:
            if not camera.isOpened(): raise ValueError('Câmera indisponível ou ocupada')
            camera.set(self.cv.CAP_PROP_FRAME_WIDTH,640);camera.set(self.cv.CAP_PROP_FRAME_HEIGHT,480)
            deadline=time.monotonic()+10
            candidate=None;hits=0
            while time.monotonic()<deadline and not stop.is_set():
                ok,frame=camera.read()
                if not ok: raise ValueError('Câmera sem imagem')
                try:
                    feature=self.feature(frame)
                    scores=sorted(((float(self.recognizer.match(feature.copy(),ref.copy(),self.cv.FaceRecognizerSF_FR_COSINE)),key) for key,ref in refs),reverse=True)
                    score,key=scores[0]
                    matched=score>=.55 and (len(scores)==1 or score-scores[1][0]>=.08)
                    hits=hits+1 if matched and key==candidate else (1 if matched else 0)
                    candidate=key if matched else None
                    if hits>=3:return candidate
                except ValueError:
                    candidate=None;hits=0
                stop.wait(.25)
            return None
        finally: camera.release()
