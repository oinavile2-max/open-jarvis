"""Tests runnable without a Windows desktop, Qt or audio devices."""
import sys
import unittest
from pathlib import Path
from datetime import datetime
from unittest.mock import patch
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from core.speaker_gain import amplify_pcm16
from core.family_gate import FamilyGate


class TestVoiceGain(unittest.TestCase):
    def test_unity_is_bit_identical(self):
        raw = np.array([-32768, -32000, -10000, 0, 10000, 32767], dtype='<i2').tobytes()
        self.assertEqual(amplify_pcm16(raw, 100), raw)

    def test_zero_is_silent(self):
        self.assertEqual(amplify_pcm16(b'\xff\x7f\x00\x80', 0), b'\x00'*4)

    def test_boost_has_limiter_and_no_overflow(self):
        raw = np.array([-32768, -20000, -9000, 0, 9000, 20000, 32767], dtype='<i2').tobytes()
        boosted = np.frombuffer(amplify_pcm16(raw, 200), dtype='<i2')
        self.assertEqual(len(boosted), 7)
        self.assertEqual(boosted[3], 0)
        self.assertGreater(boosted[4], 9000)
        self.assertLessEqual(boosted.max(), 32767)
        self.assertGreaterEqual(boosted.min(), -32768)

    def test_half_volume_quieter(self):
        raw = np.array([4000, -4000, 15000, -15000], dtype='<i2').tobytes()
        low = np.frombuffer(amplify_pcm16(raw, 50), dtype='<i2')
        self.assertTrue(all(abs(a)<abs(b) for a,b in zip(low, np.frombuffer(raw,dtype='<i2'))))


class TestFamilyGate(unittest.TestCase):
    def test_disabled_by_default(self):
        with patch('core.family_gate.load_policy', return_value={'enabled':False, 'all_present_consented':True}):
            self.assertFalse(FamilyGate().should_comment(has_useful_context=True, monotonic=10000))

    def test_requires_all_present_consent(self):
        with patch('core.family_gate.load_policy', return_value={'enabled':True, 'all_present_consented':False}):
            self.assertFalse(FamilyGate().should_comment(has_useful_context=True,monotonic=10000))

    def test_night_and_cooldown_and_private(self):
        policy={'enabled':True,'all_present_consented':True,'quiet_start':22,'quiet_end':8,
                'min_seconds_between_comments':900}
        gate=FamilyGate()
        with patch('core.family_gate.load_policy', return_value=policy):
            self.assertFalse(gate.should_comment(now=datetime(2026,10,17,23),monotonic=10000,has_useful_context=True))
            self.assertFalse(gate.should_comment(now=datetime(2026,10,17,12),monotonic=10000,has_useful_context=True, confidential=True))
            self.assertTrue(gate.should_comment(now=datetime(2026,10,17,12),monotonic=10000,has_useful_context=True))
            gate.mark_commented(10000)
            self.assertFalse(gate.should_comment(now=datetime(2026,10,17,12),monotonic=10500,has_useful_context=True))
            self.assertTrue(gate.should_comment(now=datetime(2026,10,17,12),monotonic=10900,has_useful_context=True))


class TestVideoAsset(unittest.TestCase):
    def test_exact_video_source_is_shipped(self):
        filename=ROOT/'assets/orb/esfera_referencia_usuario.mp4'
        self.assertTrue(filename.is_file())
        self.assertGreater(filename.stat().st_size, 100000)

    def test_paint_code_wired_to_reference(self):
        code=(ROOT/'ui.py').read_text(encoding='utf-8')
        self.assertIn('self._paint_reference_video(p, cx, cy, r)',code)
        self.assertIn('self._ref_video_orb.set_active',code)
        self.assertIn('self._ref_video_orb.adjust_motion',code)

if __name__ == '__main__':
    unittest.main()
