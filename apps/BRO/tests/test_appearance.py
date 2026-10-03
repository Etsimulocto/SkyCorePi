import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from appearance import validate,DEFAULTS
class AppearanceTests(unittest.TestCase):
    def test_defaults_valid(self):self.assertEqual(validate(DEFAULTS),DEFAULTS)
    def test_invalid_settings_filtered(self):
        self.assertEqual(validate({'background':'invalid','ui_size':100,'text_size':True,'ui_font':'','button':'#123456'}),{'button':'#123456'})
