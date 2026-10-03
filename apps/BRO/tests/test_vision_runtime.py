import os
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
import multiprocessing as mp
from gestures import RUNTIME

def child_probe(messages):
    try:
        from vision_runtime import restore_packages
        restore_packages()
        import mediapipe
        import numpy as np
        from gestures import HandRecognizer
        r=HandRecognizer()
        try:name,score,points=r.detect(np.zeros((240,320,3),dtype=np.uint8))
        finally:r.close()
        messages.put((sys.prefix,mediapipe.__file__,name,len(points),None))
    except Exception as exc:messages.put((None,None,None,None,repr(exc)))

class SpawnRuntimeTests(unittest.TestCase):
    def test_system_parent_venv_child_recognizer(self):
        if os.environ.get('BRO_VISION_SPAWN_TEST')!='1':self.skipTest('Cross-interpreter integration runs in CI')
        self.assertEqual(sys.prefix,sys.base_prefix,'Must test system Python parent')
        context=mp.get_context('spawn');messages=context.Queue()
        process=context.Process(target=child_probe,args=(messages,))
        mp.set_executable(str(RUNTIME))
        try:process.start()
        finally:mp.set_executable(sys.executable)
        try:
            prefix,package,name,count,error=messages.get(timeout=30)
            self.assertIsNone(error,error)
            self.assertEqual(Path(prefix),RUNTIME.parent.parent)
            self.assertIn(str(RUNTIME.parent.parent),package)
            self.assertIsNone(name);self.assertEqual(count,0)
            process.join(timeout=5)
            self.assertEqual(process.exitcode,0)
        finally:
            if process.is_alive():process.terminate();process.join(timeout=5)
            messages.close()
