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
    def test_camera_and_gesture_settings(self):
        with tempfile.TemporaryDirectory() as directory:
            prefs=Preferences(Path(directory)/'settings.json')
            prefs.save(dict(camera_mode='Hands',camera_overlay=False,camera_follow=True,camera_invert_x=True,camera_smoothing=.2,camera_range=.6,camera_center_delay=2,gesture_hold=.8,gesture_confidence=.75,gesture_bindings={'Victory':'Next speaker','bad':'Fullscreen','Thumb_Up':'bad'},gesture_enabled=True))
            d=prefs.load()
            self.assertEqual(d['camera_mode'],'Hands')
            self.assertEqual(d['camera_smoothing'],.2)
            self.assertFalse(d['camera_overlay'])
            self.assertEqual(d['gesture_bindings'],{'Victory':'Next speaker'})
            self.assertNotIn('gesture_enabled',d)
            prefs.save(dict(camera_smoothing=float('nan'),camera_range=99,camera_center_delay=-1))
            self.assertNotIn('camera_smoothing',prefs.load())
            self.assertNotIn('camera_range',prefs.load())

    def test_audio_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            p=Preferences(Path(directory)/'settings.json')
            p.save(dict(audio_input='4: USB Camera',audio_output='Auto',audio_volume=.4,audio_speed=1.2,audio_auto=True,audio_muted=False,audio_voices={'Sky':'en_US-lessac-medium','BRO':'../bad','unknown':'test'}))
            d=p.load()
            self.assertEqual(d['audio_input'],'4: USB Camera')
            self.assertEqual(d['audio_volume'],.4)
            self.assertEqual(d['audio_voices'],{'Sky':'en_US-lessac-medium'})
            self.assertTrue(d['audio_auto'])
