import unittest
import numpy as np
from core.ember_cpu import CPUEmberRenderer


class TestCPUEmber(unittest.TestCase):
    def test_live_fire_has_transparency_and_reacts_to_state(self):
        renderer=CPUEmberRenderer('economy')
        a=renderer.render('IDLE',0.,dt=.1)
        b=renderer.render('SPEAKING',1.,dt=.1)
        pixels=np.frombuffer(a,dtype=np.uint8).reshape(renderer.size,renderer.size,4)
        self.assertTrue(np.all(pixels[:,:,:3]<=pixels[:,:,3:4]))
        self.assertEqual(int(pixels[0,0,3]),0)
        self.assertGreater(int(pixels[:,:,0].max()),50)
        self.assertNotEqual(a,b)
        renderer.close()
