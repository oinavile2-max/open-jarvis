"""Download pinned, checksum-verified OpenCV Zoo models for the Windows package."""
from pathlib import Path
import hashlib
import urllib.request

ROOT=Path(__file__).resolve().parents[1]/'assets'/'face_models'
REV='47534e27c9851bb1128ccc0102f1145e27f23f98'
MODELS=[('face_detection_yunet/face_detection_yunet_2023mar.onnx','yunet.onnx','8f2383e4dd3cfbb4553ea8718107fc0423210dc964f9f4280604804ed2552fa4'),('face_recognition_sface/face_recognition_sface_2021dec.onnx','sface.onnx','0ba9fbfa01b5270c96627c4ef784da859931e02f04419c829e83484087c34e79')]
if __name__=='__main__':
 ROOT.mkdir(parents=True,exist_ok=True)
 for source,target,digest in MODELS:
  data=urllib.request.urlopen('https://media.githubusercontent.com/media/opencv/opencv_zoo/'+REV+'/models/'+source,timeout=90).read()
  if hashlib.sha256(data).hexdigest()!=digest:raise RuntimeError('Model checksum mismatch: '+target)
  (ROOT/target).write_bytes(data)
  print(target,len(data),'checksum OK')
