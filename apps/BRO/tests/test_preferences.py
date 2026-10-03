import sys,json,tempfile
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from preferences import Preferences
class PreferenceTests(unittest.TestCase):
    def test_roundtrip_and_validation(self):
        with tempfile.TemporaryDirectory() as directory:
            prefs=Preferences(Path(directory)/'settings.json')
            prefs.save(dict(model='test',detent='2',reverse=True,hues={'Sky':0.6,'Cold':float('nan')},geometry='1280x850',speaker='Sky'))
            data=prefs.load();self.assertEqual(data['model'],'test');self.assertEqual(data['hues'],{'Sky':0.6})
    def test_corrupt_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'settings.json';path.write_text('broken')
            self.assertEqual(Preferences(path).load(),{})
            path.write_text(json.dumps({'reverse':'false','detent':'99','geometry':'bad'}))
            self.assertNotIn('reverse',Preferences(path).load())
            self.assertNotIn('geometry',Preferences(path).load())
