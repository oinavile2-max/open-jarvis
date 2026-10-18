"""Reactive fire/smoke volume for systems without an OpenGL 3.3 driver.

Runs on LiveEmber's worker, never the GUI or voice callback. Lower resolution
and a frame-rate cap bound CPU use; no reference footage is embedded.
"""
from __future__ import annotations
import math
import time
import numpy as np
from scipy.ndimage import gaussian_filter, map_coordinates
from core.ember_renderer import PROFILES


class CPUEmberRenderer:
    def __init__(self, quality='balanced'):
        self.size, self.steps = {'economy': (112, 24), 'balanced': (128, 28),
                                 'premium': (160, 32)}.get(quality, (128, 28))
        self.fps = 8
        self.phase = 0.
        self._last = time.monotonic()
        self._values = np.array([1., .68, 1., .62, 0.], dtype=np.float32)
        rng = np.random.default_rng(481)
        field = gaussian_filter(rng.normal(size=(48, 48, 48)).astype(np.float32), 1.5, mode='wrap')
        self.field = np.clip(.5 + field / max(float(field.std()), .001) * .16, 0., 1.)
        axis = np.linspace(-1.48, 1.48, self.size, dtype=np.float32)
        z = np.linspace(1.32, -1.32, self.steps, dtype=np.float32)
        self.z, self.y, self.x = np.meshgrid(z, axis, axis, indexing='ij')

    def noise(self, x, y, z):
        return map_coordinates(self.field, np.array([x, y, z]), order=1, mode='grid-wrap', prefilter=False)

    def render(self, state='IDLE', amplitude=0., muted=False, dt=None):
        now = time.monotonic()
        elapsed = now-self._last if dt is None else float(dt)
        dt = min(.15, max(0., elapsed)); self._last = now
        amp = float(amplitude)
        amp = min(1., max(0., amp)) if math.isfinite(amp) else 0.
        profile = PROFILES.get(str(state).upper(), PROFILES['IDLE'])
        target = np.array([profile[0]+amp*.055, profile[1]+amp*.5,
                           profile[2]+amp*.16, profile[3], amp], dtype=np.float32)
        if muted: target = np.array([.98,.45,.65,.4,0.], dtype=np.float32)
        self._values += (target-self._values)*(1.-math.exp(-dt*6.))
        expansion, turbulence, speed, intensity, energy = self._values
        self.phase += dt*float(speed)
        t = self.phase; angle = t*.115+.18*math.sin(t*.21)
        c,s = math.cos(angle),math.sin(angle)
        x = (self.x*c+self.z*s)/expansion
        y = self.y/expansion
        z = (-self.x*s+self.z*c)/expansion
        # Coherent curling field, rather than independent random moving lines.
        qx=x+.10*np.sin(y*3.7+z*2.1+t*.36)*turbulence
        qy=y+.10*np.sin(z*3.2+x*2.2-t*.29)*turbulence
        qz=z+.10*np.sin(x*3.3+y*2.5+t*.23)*turbulence
        radial=np.sqrt(qx*qx+qy*qy+qz*qz)
        envelope=np.clip((1.12-radial)/.32,0.,1.)
        envelope=envelope*envelope*(3.-2.*envelope)
        n=self.noise(qx*9.+t*.70,qy*9.-t*1.2,qz*9.+t*.4)
        fine=self.noise(qx*17.-t*.35+9.,qy*17.+t*.6,qz*17.+5.)
        fibre=np.exp(-np.square((n*.8+fine*.2-.5)*20.))
        shell=np.exp(-np.square((radial-.80)*5.2))
        density=envelope*(.075+n*.16+fibre*2.5*shell)
        pockets=self.noise(qx*5.-t*.8+18.,qy*5.+t*.4+6.,qz*5.+3.)
        heat=np.clip((pockets+.10*(1.-radial)-.40)/.27,0.,1.)
        heat=heat*heat*(3.-2.*heat)*(.65+.35*intensity)
        inward=np.clip((1.02-radial)/.58,0.,1.)
        vein=np.power(np.maximum(0.,1.-np.abs(n-.49)*4.2),7.)
        light=np.clip(.45+.5*qy+.2*qx,.1,1.)
        ash=(.12+.72*light)*(.20+fibre*1.5)*shell
        alpha=1.-np.exp(-density*(2.64/self.steps)*3.3)
        trans=np.concatenate((np.ones_like(alpha[:1]), np.cumprod(1.-alpha[:-1],axis=0)),axis=0)
        weight=trans*alpha
        coverage=1.-np.prod(1.-alpha,axis=0)
        rgb=[]
        for low,hot,peak,ash_tint in ((.48,3.4,6.,1.),(.003,.26,1.65,1.01),(.025,.012,.20,1.05)):
            ember=low+(hot-low)*heat
            ember=ember+(peak-ember)*np.power(heat,5.)
            emission=ember*(heat*.8+vein*.85)*(.06+inward*2.2)*(.78+energy*.55)
            source=ash*ash_tint+emission
            summed=np.sum(weight*source,axis=0)
            colour=np.power(1.-np.exp(-summed*1.18),.94)
            rgb.append(np.minimum(colour,coverage))
        rgba=np.stack((*rgb,coverage),axis=-1)
        return np.asarray(np.clip(rgba*255.,0.,255.),dtype=np.uint8).tobytes()

    def close(self):
        pass
