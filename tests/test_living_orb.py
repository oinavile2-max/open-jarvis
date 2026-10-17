"""Procedural orb regression tests; no Qt, Windows or audio device needed."""
import math
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from core.living_orb import LivingOrb, motion_for


class TestLivingOrb(unittest.TestCase):
    def test_profiles_and_amplitude(self):
        quiet = motion_for('IDLE', 0)
        spoken = motion_for('SPEAKING', 1)
        listening = motion_for('LISTENING', .5)
        muted = motion_for('LISTENING', 1, muted=True)
        self.assertGreater(spoken.expansion, quiet.expansion)
        self.assertGreater(spoken.turbulence, quiet.turbulence)
        self.assertGreater(listening.intensity, quiet.intensity)
        self.assertLess(muted.intensity, listening.intensity)
        self.assertEqual(motion_for('SPEAKING', 12).expansion,
                         motion_for('SPEAKING', 1).expansion)

    def test_determinism_continuity_and_liveness(self):
        orb = LivingOrb('economy')
        a = orb.sample(10, 'IDLE')
        b = orb.sample(10, 'IDLE')
        c = orb.sample(10.02, 'IDLE')
        self.assertEqual(a.ash, b.ash)
        self.assertEqual(a.fire, b.fire)
        self.assertNotEqual(a.ash, c.ash)
        # Adjacent frames should deform smoothly: no random teleportation.
        d = a.ash[1][0] if a.ash[1] else a.ash[0][0]
        idx = next(i for i,bucket in enumerate(a.ash) if d in bucket)
        pos = a.ash[idx].index(d)
        dc = c.ash[idx][pos]
        self.assertLess(abs(dc.x1-d.x1)+abs(dc.y1-d.y1), .10)

    def test_finite_coordinates_and_quality(self):
        sizes=[]
        for quality in ('economy','balanced','premium'):
            orb = LivingOrb(quality)
            frame = orb.sample(27.3, 'THINKING', .8)
            lines = sum((len(k) for k in frame.ash+frame.fire))
            sizes.append(lines)
            self.assertEqual(len(frame.ash),4)
            self.assertEqual(len(frame.fire),4)
            self.assertEqual(len(frame.hot_spots),6)
            for bucket in frame.ash+frame.fire:
                for s in bucket:
                    self.assertTrue(all(math.isfinite(v) and abs(v)<3
                                        for v in s))
        self.assertLess(sizes[0],sizes[1]); self.assertLess(sizes[1],sizes[2])

    def test_modes_and_legacy_fallback(self):
        orb = LivingOrb('not-a-quality')
        self.assertEqual(orb.quality,'balanced')
        for state in ('IDLE', 'INITIALISING','LISTENING','PROCESSING',
                      'THINKING','EXECUTING','ERROR','SPEAKING','nonsense'):
            frame = orb.sample(0, state, .2)
            self.assertTrue(any(frame.ash))
            self.assertGreater(frame.motion.intensity,0.)


if __name__=='__main__':
    unittest.main()
