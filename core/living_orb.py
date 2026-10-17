"""Living smoke/ember orb — deterministic animation model, no Qt dependency.

Reference: user-provided video of a fluctuating, ash-grey filament shell around
red/orange molten pockets. The animation is procedural, not video playback:
pose responds to listening, thinking, playback amplitude and mute state.

Coordinates are in orb radii (normally -1.3..+1.3); no I/O, threads, textures,
external packages or GPU requirement. Rendering is deliberately separated so
it can be tested without a window or an audio device.
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import NamedTuple


class Stroke(NamedTuple):
    x1: float
    y1: float
    x2: float
    y2: float


@dataclass(frozen=True)
class OrbMotion:
    """State-to-motion mapping: amplitudes are continuous within a state."""
    expansion: float
    turbulence: float
    speed: float
    intensity: float
    accent: str


# Multipliers around quiet, gently circulating ember sphere. Do not replace
# the warm video colours completely when speech/listening occurs: the colours
# supplement, rather than erase, the visual identity of the supplied clip.
_PROFILE = {
    'IDLE': (1.00, 1.00, 1.00, 0.65, '#ff4d1e'),
    'INITIALISING': (0.92, 0.82, 0.82, 0.50, '#ff4d1e'),
    'LISTENING': (1.07, 1.22, 1.12, 0.93, '#43ddf1'),
    'THINKING': (1.04, 1.38, 1.44, 0.83, '#c47aff'),
    'PROCESSING': (1.04, 1.38, 1.44, 0.83, '#c47aff'),
    'SPEAKING': (1.07, 1.26, 1.20, 0.94, '#ffa23b'),
    'EXECUTING': (1.05, 1.16, 1.24, 0.85, '#f1bb5c'),
    'ERROR': (0.96, 1.40, 1.40, 0.93, '#ff3152'),
}
_QUALITY = {'economy': (26, 15, 48), 'balanced': (48, 24, 92),
            'premium': (72, 40, 160)}


def motion_for(state: str, amp: float, *, speaking=False, muted=False) -> OrbMotion:
    s = 'SPEAKING' if speaking else str(state or 'IDLE').upper()
    e, turbulence, speed, intensity, accent = _PROFILE.get(s, _PROFILE['IDLE'])
    amplitude = max(0., min(1., float(amp)))
    if muted:
        # Muting the mic should not stop the animation or make the object vanish.
        return OrbMotion(.98, .60, .65, .38, '#8d5560')
    return OrbMotion(e + amplitude*.085,
                     turbulence + amplitude*.43,
                     speed + amplitude*.18,
                     min(1.0, intensity + amplitude*.18), accent)


@dataclass
class OrbFrame:
    ash: tuple[list[Stroke], ...]  # back-to-front depth/brightness buckets
    fire: tuple[list[Stroke], ...]
    motes: tuple[list[tuple[float, float]], ...]
    hot_spots: list[tuple[float, float, float, float]]
    motion: OrbMotion


class LivingOrb:
    """Repeatable soft, flowing shell around embers; can be sampled at any t.

    A strand is a 3D tangent path carried by several slow advecting waves. It
    never jumps to a newly random position at a frame boundary. Multiple
    radial layers + view-depth shading create the smoke/filament illusion.
    """

    def __init__(self, quality: str = 'balanced', seed: int = 6042):
        self.quality = quality if quality in _QUALITY else 'balanced'
        rng = random.Random(seed)
        n_ash, n_fire, n_motes = _QUALITY[self.quality]
        # Each strand: latitude, longitude, offset, winding, radius, phase, size
        self.ash_strands = [self._strand(rng, fire=False) for _ in range(n_ash)]
        self.fire_strands = [self._strand(rng, fire=True) for _ in range(n_fire)]
        self.motes = [(rng.uniform(-math.pi/2, math.pi/2),
                       rng.uniform(0, math.tau), rng.random(), rng.random())
                      for _ in range(n_motes)]
        self._nodes = 23 if self.quality != 'economy' else 17

    @staticmethod
    def _strand(rng: random.Random, *, fire: bool) -> tuple:
        return (rng.uniform(-1.26, 1.26), rng.uniform(0, math.tau),
                rng.uniform(-.8, .8), rng.choice((-1, 1))*rng.uniform(.7, 2.35),
                rng.uniform(.47, .91) if fire else rng.uniform(.81, 1.04),
                rng.uniform(0., math.tau), rng.uniform(.12, .32))

    @staticmethod
    def _project(lat: float, lon: float, radius: float, t: float, seed: float,
                 motion: OrbMotion) -> tuple[float, float, float]:
        # Curling, low-frequency flow with a coherent 3D displacement field.
        curl = motion.turbulence
        radius *= 1 + curl*(.095*math.sin(2.9*lat + 2.7*lon + t*.73 + seed)
                            + .065*math.sin(4.4*lon - t*.49 + seed*1.7))
        radius *= motion.expansion * (1 + .029*math.sin(t*1.47 + seed))
        lat += curl*.09*math.sin(2.2*lon - t*.57 + seed)
        lon += curl*.10*math.cos(3.1*lat + t*.62 + seed)
        x = radius*math.cos(lat)*math.cos(lon)
        z = radius*math.cos(lat)*math.sin(lon)
        y = radius*math.sin(lat)
        # Rotate as a volume; no constant-speed static-object turn.
        yaw = t*.21 + .23*math.sin(t*.34)
        pitch = .18*math.sin(t*.27)
        cy, sy = math.cos(yaw), math.sin(yaw)
        cp, sp = math.cos(pitch), math.sin(pitch)
        xx, zz = x*cy+z*sy, z*cy-x*sy
        yy, zz = y*cp-zz*sp, y*sp+zz*cp
        persp = 1 + zz*.11
        return xx*persp, yy*persp, max(0, min(1, (zz+1.25)/2.5))

    def sample(self, t: float, state: str = 'IDLE', amp: float = 0.0,
               *, speaking: bool = False, muted: bool = False) -> OrbFrame:
        """Time is monotonic animation time in seconds, not a frame counter."""
        motion = motion_for(state, amp, speaking=speaking, muted=muted)
        # The HUD integrates the clock at motion.speed. Scaling absolute time
        # here would jump the entire shape when the mode changes.
        t = max(0., float(t))
        ash: tuple[list[Stroke], ...] = tuple([] for _ in range(4))
        fire: tuple[list[Stroke], ...] = tuple([] for _ in range(4))

        for strands, buckets in ((self.ash_strands, ash), (self.fire_strands, fire)):
            for i, (lat0, lon0, offset, winding, radius, seed, size) in enumerate(strands):
                last = None
                for j in range(self._nodes):
                    u = (j/(self._nodes-1)-.5)*2
                    # Tangential fibre distorted by travelling waves. Asymmetric
                    # layers drift past one another, without blinking/disappearing.
                    lat = lat0 + size*u + .085*math.sin(u*4 + t*.31 + seed)
                    lon = lon0 + winding*u*size*1.55 + t*(.042+.025*offset)
                    rr = radius*(1 + .07*math.sin(u*5.2 + t*.40 + seed))
                    x, y, depth = self._project(lat, lon, rr, t, seed, motion)
                    if last is not None:
                        # Depth-shade and tune by optical density; no per-stroke
                        # random flicker, which is visibly artificial on idle.
                        strength = .25 + depth*.75
                        strength *= .84 + .16*math.sin(i*.76 + seed)
                        bucket = max(0, min(3, int(strength*3.85)))
                        buckets[bucket].append(Stroke(last[0], last[1], x, y))
                    last = (x, y)

        motes = tuple([] for _ in range(4))
        for lat, lon, seed, phase in self.motes:
            # Ember flecks follow the same flow field as the filaments.
            radius = .37 + .65*seed
            x,y,depth = self._project(lat, lon+t*.08, radius, t, phase, motion)
            b = min(3, int(max(0.,depth)*3.9))
            motes[b].append((x,y))

        spots = []
        for i in range(6):
            seed = .93+i*1.29
            lat = .76*math.sin(i*1.3+t*.19)
            lon = i*2.399 + t*.17
            x,y,depth = self._project(lat, lon, .48 + .10*math.sin(t*.35+seed),
                                      t, seed, motion)
            strength = .26 + .73*depth
            spots.append((x, y, .22 + .10*math.sin(t*.61+seed)**2, strength))

        return OrbFrame(ash, fire, motes, spots, motion)
