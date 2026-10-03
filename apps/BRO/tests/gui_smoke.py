import sys
from pathlib import Path
import tkinter as tk
sys.path.insert(0,str(Path(__file__).parents[1]))
from bloomface import App,MOODS

if __name__=="__main__":
    from unittest.mock import patch
    with patch("chat.ChatPanel.detect"):
        root=tk.Tk();app=App(root,demo=True);root.update()
    for i,name in enumerate(MOODS):
        app.face.mood=i;app.draw(3.0);root.update()
        assert len(app.canvas.find_all())>40,name
    app.turn(1);app.tap();app.weird();app.draw(3.1);root.update()
    app.copy_log();assert "WEIRD BURST" in root.clipboard_get()
    # Verify speaker labels, text editing, panel toggles and session boundaries.
    from console import SPEAKERS
    from types import SimpleNamespace
    from console import SPEAKER_HUES
    for speaker in SPEAKERS:
        app.console.speaker.set(speaker)
        assert app.face.hue==SPEAKER_HUES[speaker]
    app.face.hue=0.23
    app.console.speaker.set("Sky");app.console.speaker.set("GRIT")
    assert app.face.hue==0.23,"Color knob changes stay with their speaker"
    app.console.speaker_hues=dict(SPEAKER_HUES)
    app.console.speaker.set("BRO")
    for speaker in SPEAKERS:
        app.console.speaker.set(speaker)
        assert app.console.show_output(speaker,"Hello "+speaker,source="manual test")
    assert all(speaker+" [manual test]" in app.console.speech.get("1.0","end") for speaker in SPEAKERS)
    app.console.copy_speech();assert "GRIT [manual test]" in root.clipboard_get()
    before=app.face.control
    app.keyboard(SimpleNamespace(widget=app.console.draft),app.tap)
    assert app.face.control==before,"Typing must not trigger face controls"
    app.console.developer.set(False);app.console.toggle_dev();root.update()
    from unittest.mock import patch
    with patch.object(app.console.camera_feed,"start") as start:
        app.console.camera_visible.set(True);app.console.toggle_camera();root.update()
        start.assert_called_once()
    import tkinter as tk
    photo=tk.PhotoImage(data=b"P6\n2 1\n255\n"+bytes([255,0,0,0,255,0]),format="PPM")
    assert photo.width()==2 and photo.height()==1
    assert app.console.developer.get() and app.console.camera.winfo_ismapped()
    chat=app.console.chat
    from unittest.mock import patch
    with patch.object(chat,"worker") as worker:
        app.console.speaker.set("Sky")
        chat.entry.insert("1.0","Hello")
        chat.send()
        assert chat.busy
        old_epoch=chat.epoch
    app.console.toggle_session()
    chat.events.put((old_epoch,"reply",("Sky","Hello","stale reply",[]),None))
    chat.poll()
    assert "stale reply" not in app.console.speech.get("1.0","end")
    before=(app.face.mood,app.face.control,app.face.surprise)
    app.turn(1);app.tap();app.weird()
    assert before==(app.face.mood,app.face.control,app.face.surprise)
    assert app.usb.port is None
    assert not app.console.show_output("BRO","Must not publish after session end")
    app.console.toggle_session();app.face.control=0;app.turn(1)
    assert app.face.mood!=before[0]
    assert app.face.detent==2
    app.console.speaker.set("Sky")
    with patch.object(chat,"worker"):
        chat.entry.insert("1.0","hello");chat.send()
    assert chat.phase=="THINKING"
    app.console.speaker.set("Monday")
    chat.events.put((chat.epoch,"reply",("Sky","hello","Hello Architect!",[]),None));chat.poll()
    assert chat.phase=="REPLYING" and "Sky [local AI]: Hello Architect!" in app.console.speech.get("1.0","end")
    chat.backend.commit("Monday","hi","hey")
    app.console.speaker.set("Sky");chat.clear_selected()
    assert chat.backend.histories["Sky"]==[] and chat.backend.histories["Monday"]
    chat.phase_until=0;chat.poll();assert chat.phase=="IDLE"
    with patch.object(chat,"worker"):
        chat.entry.insert("1.0","retry");chat.send()
    chat.events.put((chat.epoch,"reply",None,"connection refused"));chat.poll()
    assert chat.phase=="ERROR" and not chat.busy
    assert "connection refused" in chat.diagnostic_summary()
    pad=app.console.gamepad
    with patch.object(pad,"save"),patch.object(pad,"dispatch") as dispatch:
        pad.action.set("Weird burst");pad.learn();pad.handle("button12")
        assert pad.bindings["button12"]=="Weird burst"
        dispatch.assert_not_called()
        pad.handle("button12");dispatch.assert_called_once_with("Weird burst")
    app.console.speaker.set("BRO");pad.dispatch("Next speaker")
    assert app.console.speaker.get()=="Sky"
    pad.dispatch("Look left");assert app.face.gaze==-1
    pad.dispatch("Center gaze");assert app.face.gaze==0
    app.console.camera_visible.set(False);app.console.toggle_camera()
    app.console.speaker.set("BRO")
    dashboard=app.console.dashboard
    dashboard.poll()
    assert "USB: disconnected" in dashboard.summary()
    assert "Speaker:" in dashboard.summary()
    dashboard.copy();assert "Chat diagnostics:" in root.clipboard_get()
    look=app.appearance
    look.open();root.update()
    look.variables["panel_border"].set("#221133")
    look.variables["face_background"].set("#112233")
    look.variables["button"].set("#334455")
    look.variables["ui_size"].set("13")
    look.variables["face_font"].set("DejaVu Sans")
    assert look.update()
    assert app.console.draft.cget("highlightbackground")=="#221133" and app.canvas.cget("bg")=="#112233"
    from tkinter import ttk
    assert ttk.Style().lookup("TButton","background")=="#334455"
    app.draw(3.0);root.update()
    look.variables["panel_border"].set("broken");assert not look.update()
    look.reset();look.window.destroy()
    feed=app.console.camera_feed
    feed.mode.set("Face");feed.configure_vision()
    feed.observation({'target':(0.8,-0.5),'count':1,'ms':10,'error':''})
    assert feed.target==(0.8,-0.5) and "tracking" in feed.vision_status.get()
    app.draw(3);feed.mode.set("Off");feed.configure_vision()
    assert feed.target is None
    feed.poll()
    gestures=feed.gestures
    with patch.object(app,'save_preferences'),patch.object(app.console.gamepad,'dispatch') as dispatch:
        gestures.signal.set('Victory');gestures.action.set('Next speaker');gestures.assign()
        assert gestures.bindings['Victory']=='Next speaker'
        gestures.observation({'gesture':'Victory','confidence':.9})
        dispatch.assert_not_called()
        gestures.enabled.set(True)
        with patch('gestures.time.monotonic',side_effect=[1,1.3,1.7]):
            for _ in range(3):gestures.observation({'gesture':'Victory','confidence':.9})
        dispatch.assert_called_once_with('Next speaker')
        feed.smoothing.set(.25);feed.gaze_range.set(.5);feed.center_delay.set(2);feed.settings_changed()
        assert 'range 50%' in feed.tracking_values.get()

    app.face.mood=0;app.draw(3.0);root.update()
    try:
        from PIL import ImageGrab
        ImageGrab.grab().save('/tmp/bloomface-preview.png')
    except ImportError:pass
    app.close()
    print('All expressions, controls, drawing and clipboard: PASS')
