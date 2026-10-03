import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from vision import choose_target,normalized_center
class VisionTests(unittest.TestCase):
    def test_largest_then_nearest(self):
        boxes=[(0,0,20,20),(100,100,40,40)]
        self.assertEqual(choose_target(boxes),boxes[1])
        self.assertEqual(choose_target(boxes,(5,5)),boxes[0])
        self.assertIsNone(choose_target([]))
    def test_coordinates(self):
        self.assertEqual(normalized_center((40,40,20,20),100,100),(0,0))
        self.assertEqual(normalized_center((0,0,10,10),100,100),(-0.9,-0.9))

class DetectorTests(unittest.TestCase):
    def test_real_blank_face_and_motion(self):
        try:
            import cv2
            import numpy as np
        except ImportError:self.skipTest('OpenCV not installed locally')
        from vision import Tracker
        tracker=Tracker(cv2)
        frame=np.zeros((240,320,3),dtype=np.uint8)
        report=tracker.process(frame.copy(),1,False)
        self.assertEqual(report['error'],'')
        self.assertIsNone(report['target'])
        tracker.process(frame.copy(),2,False)
        frame[50:100,70:120]=255
        tracker.last=0
        report=tracker.process(frame,2,True)
        self.assertGreater(report['count'],0)
        self.assertIsNotNone(report['target'])
