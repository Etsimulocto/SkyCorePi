import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import json
import os
os.environ["ORT_DISABLE_TELEMETRY"]="1"
import unittest
from audio_worker import resolve_device,transcribe_chunks

def device(i,name,inputs=1,outputs=0,default_input=False,default_output=False):
    return dict(index=i,name=name,inputs=inputs,outputs=outputs,rate=48000,default_input=default_input,default_output=default_output)

class DeviceTests(unittest.TestCase):
    def test_auto_prefers_camera_usb_input_and_default_output(self):
        rows=[device(0,'Built in',default_input=True),device(1,'USB speaker',0,2),device(2,'Arducam USB Camera'),device(3,'HDMI headphones',0,2,default_output=True)]
        self.assertEqual(resolve_device(rows,'Auto','input'),2)
        self.assertEqual(resolve_device(rows,'Auto','output'),3)
    def test_saved_name_survives_index_change_and_missing_reports(self):
        self.assertEqual(resolve_device([device(9,'USB Camera')],'2: USB Camera','input'),9)
        with self.assertRaisesRegex(RuntimeError,'unavailable'):resolve_device([device(9,'other')],'2: USB Camera','input')
        with self.assertRaisesRegex(RuntimeError,'No input'):resolve_device([device(0,'speaker',0,2)],'Auto','input')
    def test_duplicate_name_requires_valid_index(self):
        rows=[device(1,'USB Mic'),device(2,'USB Mic')]
        self.assertEqual(resolve_device(rows,'2: USB Mic','input'),2)
        with self.assertRaisesRegex(RuntimeError,'ambiguous'):resolve_device(rows,'9: USB Mic','input')

class TranscriptTests(unittest.TestCase):
    def test_segments_and_final_are_combined(self):
        class Recognizer:
            def AcceptWaveform(self,data):return data==b'first'
            def Result(self):return json.dumps(dict(text='hello'))
            def FinalResult(self):return json.dumps(dict(text='architect'))
        self.assertEqual(transcribe_chunks([b'first',b'second'],Recognizer()),'hello architect')

class AudioModelTests(unittest.TestCase):
    def test_real_piper_synthesis(self):
        if os.environ.get('BRO_AUDIO_TEST')!='1':self.skipTest('Optional audio model integration runs in CI')
        import io,wave
        from piper import PiperVoice,SynthesisConfig
        from audio_worker import VOICES
        voice=PiperVoice.load(str(VOICES/'en_US-lessac-medium.onnx'))
        chunks=list(voice.synthesize('Hello Architect.',syn_config=SynthesisConfig(volume=.5,length_scale=1)))
        self.assertTrue(chunks)
        self.assertGreater(sum(len(c.audio_int16_bytes) for c in chunks),1000)
        self.assertGreater(chunks[0].sample_rate,8000)
    def test_real_vosk_recorded_fixture(self):
        if os.environ.get('BRO_AUDIO_TEST')!='1':self.skipTest('Optional audio model integration runs in CI')
        import io,wave,urllib.request
        from vosk import Model,KaldiRecognizer,SetLogLevel
        from audio_worker import VOSK_MODEL
        SetLogLevel(-1)
        data=urllib.request.urlopen('https://raw.githubusercontent.com/alphacep/vosk-api/master/python/example/test.wav',timeout=30).read()
        with wave.open(io.BytesIO(data)) as wav:
            self.assertEqual(wav.getnchannels(),1)
            r=KaldiRecognizer(Model(str(VOSK_MODEL)),wav.getframerate())
            chunks=[]
            while chunk:=wav.readframes(4000):chunks.append(chunk)
        text=transcribe_chunks(chunks,r)
        self.assertIn('one',text)
        self.assertIn('zero',text)

class EngineTests(unittest.TestCase):
    def test_cancel_terminates_worker_and_invalidates_events(self):
        import tempfile
        from unittest.mock import patch
        import audio
        engine=audio.AudioEngine()
        with tempfile.TemporaryDirectory() as directory:
            worker=Path(directory)/'worker.py'
            worker.write_text("import json,sys,time\njson.loads(sys.stdin.readline())\nprint(json.dumps({'kind':'status','text':'ready'}),flush=True)\ntime.sleep(60)\n")
            with patch.object(audio,'RUNTIME',Path(sys.executable)),patch.object(audio,'WORKER',worker):
                try:
                    engine.run(dict(operation='speak'))
                    epoch,event=engine.events.get(timeout=5)
                    self.assertEqual(event['text'],'ready')
                    process=engine.process
                    engine.cancel()
                    self.assertNotEqual(epoch,engine.epoch)
                    self.assertIsNotNone(process.poll())
                finally:engine.cancel()

class OutputTests(unittest.TestCase):
    def test_mono_voice_becomes_stereo_at_device_rate(self):
        try:import numpy as np
        except ImportError:self.skipTest('NumPy runs in audio integration environment')
        from audio_worker import prepare_output
        source=np.full(2205,1234,dtype=np.int16)
        data=prepare_output(source.tobytes(),22050,48000,1,2)
        frames=np.frombuffer(data,dtype=np.int16).reshape(-1,2)
        self.assertEqual(len(frames),4800)
        self.assertTrue(np.all(frames[:,0]==frames[:,1]))
        self.assertTrue(np.all(frames==1234))
