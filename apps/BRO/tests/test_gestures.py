import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from gestures import GestureGate

class GateTests(unittest.TestCase):
    def test_hold_release_and_no_repeat(self):
        g=GestureGate()
        self.assertIsNone(g.update('Victory',.9,0))
        self.assertIsNone(g.update('Victory',.9,.3))
        self.assertEqual(g.update('Victory',.9,.6),'Victory')
        self.assertIsNone(g.update('Victory',.9,.9))
        self.assertIsNone(g.update('Thumb_Up',.9,1.2),'Changing gesture must not bypass release')
        for t in (1.4,1.6,1.9):self.assertIsNone(g.update(None,0,t))
        self.assertIsNone(g.update('Thumb_Up',.9,2))
        self.assertIsNone(g.update('Thumb_Up',.9,2.3))
        self.assertEqual(g.update('Thumb_Up',.9,2.7),'Thumb_Up')
    def test_confidence_and_stalls(self):
        g=GestureGate()
        g.update('Victory',.9,0)
        self.assertIsNone(g.update('Victory',.9,4),'A stalled camera does not count as holding')
        g.update('Victory',.1,4.2)
        self.assertIsNone(g.update('Victory',.9,4.4))
        self.assertIsNone(g.update('Victory',.9,4.7))
        self.assertEqual(g.update('Victory',.9,5.1),'Victory')
        g.update(None,0,5.2)
        self.assertIsNone(g.update(None,0,7),'A stalled camera does not count as release')
        self.assertTrue(g.latched)

class RecognizerTests(unittest.TestCase):
    def test_real_model_blank_frame(self):
        import os
        if os.environ.get('BRO_VISION_TEST')!='1':self.skipTest('Optional vision runtime integration runs in CI')
        import numpy as np
        from gestures import HandRecognizer
        r=HandRecognizer()
        try:
            name,score,points=r.detect(np.zeros((240,320,3),dtype=np.uint8))
            self.assertIsNone(name)
            self.assertEqual(points,[])
        finally:r.close()

    def test_real_model_thumb_up(self):
        import os
        if os.environ.get('BRO_VISION_TEST')!='1':self.skipTest('Optional vision runtime integration runs in CI')
        import hashlib
        import urllib.request
        import cv2
        import numpy as np
        from gestures import HandRecognizer
        # Google's published MediaPipe test image; no user photos.
        data=urllib.request.urlopen('https://storage.googleapis.com/mediapipe-assets/thumb_up.jpg',timeout=30).read()
        self.assertEqual(hashlib.sha256(data).hexdigest(),'5d673c081ab13b8a1812269ff57047066f9c33c07db5f4178089e8cb3fdc0291')
        frame=cv2.imdecode(np.frombuffer(data,dtype=np.uint8),cv2.IMREAD_COLOR)
        r=HandRecognizer()
        try:
            name,score,points=r.detect(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB))
            self.assertEqual(name,'Thumb_Up')
            self.assertGreater(score,.7)
            self.assertEqual(len(points),21)
        finally:r.close()
