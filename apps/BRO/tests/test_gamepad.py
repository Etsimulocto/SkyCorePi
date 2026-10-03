import sys,struct
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from gamepad import Decoder

def event(value,kind,number=0):return struct.pack('<IhBB',0,value,kind,number)
class DecoderTests(unittest.TestCase):
    def test_startup_does_not_act(self):
        d=Decoder();self.assertIsNone(d.event(event(1,0x81)))
        self.assertIsNone(d.event(event(1,1)))
        d.event(event(0,1));self.assertEqual(d.event(event(1,1)),'button0')
    def test_deadzone_and_latching(self):
        d=Decoder();self.assertIsNone(d.event(event(5000,2)))
        self.assertEqual(d.event(event(25000,2)),'axis0+')
        self.assertIsNone(d.event(event(30000,2)))
        d.event(event(0,2));self.assertEqual(d.event(event(-25000,2)),'axis0-')
