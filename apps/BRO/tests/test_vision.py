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
