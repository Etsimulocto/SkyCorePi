"""Isolated audio operations. JSON stdout; native library logs stay on stderr."""
import json
import os
os.environ["ORT_DISABLE_TELEMETRY"]="1"
import math
from pathlib import Path
import queue
import sys
import threading
import time

CACHE=Path.home()/'.cache'/'skycorepi'/'audio'
VOICES=CACHE/'voices'
VOSK_MODEL=CACHE/'vosk-model-small-en-us-0.15'

def emit(kind,**values):print(json.dumps(dict(kind=kind,**values)),flush=True)

def device_rows(sd):
    defaults=sd.default.device
    return [dict(index=i,name=d['name'],inputs=d['max_input_channels'],outputs=d['max_output_channels'],rate=d['default_samplerate'],default_input=i==defaults[0],default_output=i==defaults[1]) for i,d in enumerate(sd.query_devices())]

def resolve_device(rows,selection,direction):
    field='inputs' if direction=='input' else 'outputs'
    usable=[d for d in rows if d[field]>0]
    if not usable:raise RuntimeError('No '+direction+' device detected. Check USB/audio settings, then rescan.')
    if selection!='Auto':
        # Preserve the name when enumeration indices change after reconnect.
        name=selection.split(': ',1)[-1]
        matches=[d for d in usable if d['name']==name]
        exact=next((d for d in matches if selection==str(d['index'])+': '+d['name']),None)
        if exact:return exact['index']
        if len(matches)==1:return matches[0]['index']
        raise RuntimeError('Selected '+direction+' device unavailable or ambiguous; rescan and select it.')
    if direction=='input':
        usb=[d for d in usable if any(t in d['name'].lower() for t in ('arducam','usb','camera'))]
        if usb:return usb[0]['index']
    default=next((d for d in usable if d['default_'+direction]),None)
    return (default or usable[0])['index']

def transcribe_chunks(chunks,recognizer):
    parts=[]
    for data in chunks:
        if recognizer.AcceptWaveform(data):
            text=json.loads(recognizer.Result()).get('text','').strip()
            if text:parts.append(text)
    final=json.loads(recognizer.FinalResult()).get('text','').strip()
    if final:parts.append(final)
    return ' '.join(parts)

def speak(request,sd):
    from piper import PiperVoice,SynthesisConfig
    import numpy as np
    voice=request['voice']
    if Path(voice).name!=voice:raise ValueError('Invalid voice name')
    path=VOICES/(voice+'.onnx')
    if not path.is_file():raise RuntimeError('Voice missing; run bash apps/BRO/install_audio.sh')
    device=resolve_device(device_rows(sd),request['output'],'output')
    emit('status',text='Loading voice: '+voice)
    engine=PiperVoice.load(str(path))
    config=SynthesisConfig(volume=float(request['volume']),length_scale=1/float(request['speed']))
    stream=None
    try:
        for chunk in engine.synthesize(request['text'][:4000],syn_config=config):
            if stream is None:
                stream=sd.RawOutputStream(device=device,samplerate=chunk.sample_rate,channels=chunk.sample_channels,dtype='int16')
                stream.start();emit('status',text='Speaking · '+str(sd.query_devices(device)['name']))
            stream.write(chunk.audio_int16_bytes)
        if stream is not None:stream.stop()
    finally:
        if stream is not None:stream.close()
    emit('done',text='Speech finished')

def listen(request,sd):
    import numpy as np
    from vosk import Model,KaldiRecognizer,SetLogLevel
    if not VOSK_MODEL.is_dir():raise RuntimeError('Speech recognition model missing; run bash apps/BRO/install_audio.sh')
    device=resolve_device(device_rows(sd),request['input'],'input')
    rate=int(sd.query_devices(device)['default_samplerate'])
    sd.check_input_settings(device=device,channels=1,dtype='int16',samplerate=rate)
    SetLogLevel(-1);emit('status',text='Loading microphone recognizer…')
    recognizer=KaldiRecognizer(Model(str(VOSK_MODEL)),rate)
    stopped=threading.Event()
    def control():
        for line in sys.stdin:
            if line.strip()=='stop':stopped.set();break
    threading.Thread(target=control,daemon=True).start()
    blocks=queue.Queue(maxsize=64);overflow=threading.Event()
    def callback(data,frames,timing,status):
        if status:overflow.set()
        try:blocks.put_nowait(bytes(data))
        except queue.Full:overflow.set()
    parts=[];started=time.monotonic();next_meter=0
    with sd.RawInputStream(device=device,samplerate=rate,blocksize=max(800,int(rate*.1)),channels=1,dtype='int16',callback=callback):
        emit('status',text='Listening · '+str(sd.query_devices(device)['name'])+' · maximum 20 seconds')
        while not stopped.is_set() and time.monotonic()-started<20:
            try:data=blocks.get(timeout=.1)
            except queue.Empty:continue
            if recognizer.AcceptWaveform(data):
                text=json.loads(recognizer.Result()).get('text','').strip()
                if text:parts.append(text)
            now=time.monotonic()
            if now>=next_meter:
                samples=np.frombuffer(data,dtype=np.int16).astype(float)/32768
                level=math.sqrt(float(np.mean(samples*samples))) if len(samples) else 0
                emit('level',value=round(level,4));next_meter=now+.2
    # Process the bounded tail after closing capture, then finalize once.
    tail=[]
    while not blocks.empty():tail.append(blocks.get_nowait())
    text=transcribe_chunks(tail,recognizer)
    if text:parts.append(text)
    if overflow.is_set():emit('status',text='Microphone overflow reported; some audio may have been lost')
    emit('transcript',text=' '.join(parts)[:4000])

def main():
    try:
        request=json.loads(sys.stdin.readline())
        import sounddevice as sd
        op=request['operation']
        if op=='devices':
            emit('devices',rows=device_rows(sd),voices=sorted(p.stem for p in VOICES.glob('*.onnx') if p.with_suffix('.onnx.json').is_file()))
        elif op=='speak':speak(request,sd)
        elif op=='listen':listen(request,sd)
        else:raise ValueError('Unknown audio operation')
    except Exception as exc:
        emit('error',text=str(exc));return 1
    return 0

if __name__=='__main__':raise SystemExit(main())
