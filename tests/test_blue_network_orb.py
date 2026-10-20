import math
import unittest
from core.blue_network_orb import BlueNetworkOrb


class TestBlueNetwork(unittest.TestCase):
    def test_edges_valid_and_geometry_finite(self):
        orb=BlueNetworkOrb()
        self.assertTrue(orb.edges)
        self.assertEqual(len(orb.edges),len(set(orb.edges)))
        self.assertTrue(all(0<=a<b<len(orb.nodes) for a,b in orb.edges))
        self.assertTrue(all(math.isfinite(x) for p in orb.frame(3,.5) for x in p))

    def test_pulses_and_moves(self):
        orb=BlueNetworkOrb()
        quiet=orb.frame(1,0)
        loud=orb.frame(1,1)
        radius=lambda points:sum(x*x+y*y for x,y,z in points)
        self.assertGreater(radius(loud),radius(quiet))
        self.assertNotEqual(quiet,orb.frame(2,0))
