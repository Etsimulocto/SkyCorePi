"""Explicit local Ollama service controls with verified shutdown reporting."""
import json
import subprocess
import urllib.request
import shutil
from pathlib import Path

URL='http://127.0.0.1:11434'

def api(path,payload=None):
    request=urllib.request.Request(URL+path,data=None if payload is None else json.dumps(payload).encode(),headers={'Content-Type':'application/json'})
    with urllib.request.urlopen(request,timeout=2) as response:return json.loads(response.read())

def reachable():
    try:api('/api/tags');return True
    except Exception:return False

def service(action):
    systemctl=shutil.which('systemctl')
    if not systemctl:return False
    for command in (["sudo","-n",systemctl,action,'ollama.service'],[systemctl,'--user','--no-ask-password',action,'ollama.service']):
        try:
            if subprocess.run(command,capture_output=True,text=True,timeout=5).returncode==0:return True
        except (OSError,subprocess.TimeoutExpired):pass
    return False

def stop():
    if not reachable():return 'Ollama already stopped / unreachable'
    service('stop')
    if not reachable():return 'Ollama stopped · local endpoint offline'
    unloaded=[];errors=[]
    try:
        for model in api('/api/ps').get('models',[])[:8]:
            name=model.get('name') or model.get('model')
            if not name:continue
            try:api('/api/generate',{'model':name,'keep_alive':0});unloaded.append(name)
            except Exception as exc:errors.append(str(exc))
    except Exception as exc:errors.append(str(exc))
    return 'Ollama service still running; unloaded models: '+(', '.join(unloaded) or 'none')+'. Re-run bash install_pi.sh to enable service stop.'+(' Errors: '+'; '.join(errors) if errors else '')

def start():
    if reachable():return 'Ollama already running'
    if service('start'):return 'Ollama service started · use Check Ollama'
    return 'Could not start Ollama. Re-run bash install_pi.sh or start its service manually.'

def shutdown_report():
    result=stop()
    print(result,flush=True)
    try:
        path=Path.home()/'.cache'/'skycorepi'/'ai-shutdown.txt';path.parent.mkdir(parents=True,exist_ok=True);path.write_text(result+'\n')
    except OSError:pass
    return result
