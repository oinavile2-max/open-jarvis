"""Original procedural point network inspired by the user's blue sphere reference.
No external scene, web view, model download or GPU is required.
"""
import math


class BlueNetworkOrb:
    def __init__(self, count=360):
        self.nodes = []
        golden = math.pi*(3-math.sqrt(5))
        for i in range(count):
            y = 1-2*(i+.5)/count
            rr = math.sqrt(max(0, 1-y*y))
            angle = i*golden
            radius = .60+.28*((i*37)%97)/97 if i%7==0 else .96+.04*math.sin(i*1.73)
            self.nodes.append((math.cos(angle)*rr*radius, y*radius, math.sin(angle)*rr*radius))
        self.edges = set()
        for i, a in enumerate(self.nodes):
            nearby = sorted((sum((x-y)**2 for x,y in zip(a,b)), j)
                            for j,b in enumerate(self.nodes) if i != j)
            for distance,j in nearby[:5]:
                if distance < .18 and (i+j)%9 != 0:
                    self.edges.add(tuple(sorted((i,j))))
        self.edges = sorted(self.edges)

    def frame(self, seconds, amplitude=0, state='IDLE'):
        amplitude = max(0.,min(1.,float(amplitude)))
        pulse = 1+.018*math.sin(seconds*2)+amplitude*.095
        angle = seconds*.14
        ca,sa = math.cos(angle),math.sin(angle)
        tilt = .18+.10*math.sin(seconds*.27)
        ct,st = math.cos(tilt),math.sin(tilt)
        speed = 2.5 if state in ('THINKING','PROCESSING') else 1.2
        points=[]
        for i,(x,y,z) in enumerate(self.nodes):
            ripple = 1+.012*math.sin(seconds*speed+i*.37)+amplitude*.014*math.sin(i*.8+seconds*5)
            xx,zz=x*ca+z*sa,-x*sa+z*ca
            yy,zz=y*ct-zz*st,y*st+zz*ct
            perspective=1/(1-zz*.13)
            points.append((xx*ripple*pulse*perspective,yy*ripple*pulse*perspective,zz))
        return points


def paint_blue_network(painter, model, cx, cy, radius, seconds, amplitude, state):
    from PyQt6.QtCore import QPointF
    from PyQt6.QtGui import QColor, QPen
    points=model.frame(seconds,amplitude,state)
    painter.save()
    for a,b in model.edges:
        x,y,z=points[a];u,v,w=points[b]
        alpha=int(12+48*(min(z,w)+1)/2)
        painter.setPen(QPen(QColor(60,174,222,alpha),.55))
        painter.drawLine(QPointF(cx+x*radius,cy+y*radius),QPointF(cx+u*radius,cy+v*radius))
    painter.setPen(QPen(QColor(106,207,248,190),1))
    for x,y,z in points:
        painter.setPen(QPen(QColor(106,207,248,int(45+150*(z+1)/2)),1.0+max(0,z)*.55))
        painter.drawPoint(QPointF(cx+x*radius,cy+y*radius))
    painter.restore()
