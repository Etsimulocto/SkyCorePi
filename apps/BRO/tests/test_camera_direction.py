import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from types import SimpleNamespace
from unittest.mock import Mock
import queue
import time
from camera import CameraPanel

class CameraDirectionTests(unittest.TestCase):
    def test_toggle_reverses_camera_gaze_only(self):
        panel=CameraPanel.__new__(CameraPanel)
        panel.process=Mock();panel.process.is_alive.return_value=True
        panel.mode=Mock();panel.mode.get.return_value='Motion'
        panel.follow=Mock();panel.follow.get.return_value=True
        panel.invert_x=Mock()
        panel.target=(0.8,0.4);panel.target_at=time.monotonic()
        panel.gaze_y=0;panel.messages=queue.Queue()
        panel.started=time.monotonic();panel.received=True
        panel.app=SimpleNamespace(face=SimpleNamespace(gaze=0),console=SimpleNamespace(active=True))
        for inverted,expected in ((False,0.096),(True,-0.096)):
            panel.invert_x.get.return_value=inverted
            panel.app.face.gaze=0;panel.gaze_y=0
            panel.poll()
            self.assertAlmostEqual(panel.app.face.gaze,expected)
            self.assertAlmostEqual(panel.gaze_y,0.048)
            self.assertEqual(panel.target,(0.8,0.4))
