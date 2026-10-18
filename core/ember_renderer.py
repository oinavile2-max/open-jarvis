"""GPU volume renderer, independent of Qt and the audio capture thread."""
from __future__ import annotations
import math
import os
import time
from pathlib import Path

VERTEX = '''#version 330
void main(){
 vec2 p=vec2((gl_VertexID<<1)&2,gl_VertexID&2);
 gl_Position=vec4(p*2.-1.,0.,1.);
}'''
PROFILES = {
    'IDLE': (1.0, .68, 1.0, .62),
    'LISTENING': (1.045, 1.05, 1.10, .80),
    'THINKING': (1.01, 1.25, 1.26, .78),
    'PROCESSING': (1.01, 1.25, 1.26, .78),
    'SPEAKING': (1.055, 1.10, 1.10, .95),
    'EXECUTING': (1.035, 1.12, 1.19, .90),
    'ERROR': (.97, 1.32, .88, .82),
}
BUDGETS = {'economy': (256, 36, 20), 'balanced': (384, 56, 30),
           'premium': (512, 80, 30)}

class EmberRenderer:
    def __init__(self, quality='balanced', backend=None, neon_strength=1.0):
        import moderngl
        self.quality=quality if quality in BUDGETS else 'balanced'
        self.size,self.steps,self.fps=BUDGETS[self.quality]
        self.neon_strength=max(0.,min(2.,float(neon_strength)))
        kwargs={'require':330}
        if backend: kwargs['backend']=backend
        elif os.name=='posix' and not os.environ.get('DISPLAY'): kwargs['backend']='egl'
        self.ctx=moderngl.create_standalone_context(**kwargs)
        shader=Path(__file__).resolve().parents[1]/'assets'/'shaders'/'ember_volume.frag'
        try:
            self.program=self.ctx.program(vertex_shader=VERTEX,fragment_shader=shader.read_text())
            self.vao=self.ctx.vertex_array(self.program,[])
            self.scene_texture=self.ctx.texture((self.size,self.size),components=4)
            self.scene_texture.filter=(moderngl.LINEAR,moderngl.LINEAR)
            self.scene_texture.repeat_x=False;self.scene_texture.repeat_y=False
            self.volume_fbo=self.ctx.framebuffer(color_attachments=[self.scene_texture])
            self.fbo=self.ctx.simple_framebuffer((self.size,self.size),components=4)
            self.bloom=self.ctx.program(vertex_shader=VERTEX,fragment_shader=shader.with_name('ember_bloom.frag').read_text())
            self.bloom_vao=self.ctx.vertex_array(self.bloom,[])
            self.bloom['scene'].value=0
            self.bloom['resolution'].value=(self.size,self.size)
        except Exception:
            self.ctx.release()
            raise
        self.phase=0.0
        self._last=time.monotonic()
        self._values=[1.,.68,1.,.62,0.]

    def render(self,state='IDLE',amplitude=0.,muted=False,dt=None):
        now=time.monotonic()
        dt=min(.1,max(0.,now-self._last if dt is None else float(dt)))
        self._last=now
        amp=float(amplitude)
        amp=max(0.,min(1.,amp)) if math.isfinite(amp) else 0.
        profile=PROFILES.get(str(state).upper(),PROFILES['IDLE'])
        targets=[profile[0]+amp*.055,profile[1]+amp*.50,
                 profile[2]+amp*.16,profile[3],amp]
        if muted: targets=[.98,.45,.65,.40,0.]
        blend=1.-math.exp(-dt*6.)
        self._values=[v+(target-v)*blend for v,target in zip(self._values,targets)]
        exp,turb,speed,intensity,level=self._values
        self.phase+=dt*speed
        self.volume_fbo.use();self.volume_fbo.clear(0.,0.,0.,0.)
        for key,value in {'resolution':(self.size,self.size),'phase':self.phase,
                          'energy':level,'turbulence':turb,'expansion':exp,
                          'intensity':intensity,'quality_steps':self.steps}.items():
            self.program[key].value=value
        self.vao.render(vertices=3)
        self.fbo.use();self.fbo.clear(0.,0.,0.,0.)
        self.scene_texture.use(location=0)
        self.bloom['neon_strength'].value=self.neon_strength
        self.bloom_vao.render(vertices=3)
        return self.fbo.read(components=4,alignment=1)

    def close(self):
        for obj in (self.fbo,self.volume_fbo,self.scene_texture,self.bloom_vao,self.bloom,self.vao,self.program,self.ctx): obj.release()
