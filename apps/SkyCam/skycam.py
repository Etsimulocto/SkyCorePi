# skycam.py
# run with: python3 ~/SkyCam/skycam.py
# path: /home/quarterbitgames/SkyCam/skycam.py
# description: BloomCore SkyCam tuned for Arducam 8MP USB Camera.
# version: 1.7
# format: bloomcore/v1.3

import cv2, subprocess, tempfile, os, time, shutil, tkinter as tk
from PIL import Image, ImageTk

BASE=os.path.expanduser("~/SkyCam")
CAPTURES=os.path.join(BASE,"captures")
os.makedirs(CAPTURES,exist_ok=True)

# CAMERA is discovered dynamically. Do not hardcode /dev/videoN: USB/V4L2 node
# numbers can change and this Arducam also exposes a metadata-only node.
CAMERA=None
PREFERRED_CAMERA_TEXT="Arducam 8MP USB Camera"
PREFERRED_CAMERA_SERIAL="AC20251017V0"
WIDTH,HEIGHT,FPS=1280,720,30

BG="#050505"; FG="#ffffff"; BTN_BG="#1b1b1b"; ACTIVE="#333333"
GOOD="#7CFF7C"; WARN="#FFD36A"

cap=None
last_frame=None
rotation=0
digital_zoom=1.0
video_photo=None
video_item=None


def set_status(text, good=True):
    status.config(text=text, fg=GOOD if good else WARN)


def video_devices():
    devices=[]
    try:
        for name in os.listdir("/dev"):
            if not name.startswith("video"):
                continue
            suffix=name[5:]
            if suffix.isdigit():
                devices.append((int(suffix),f"/dev/{name}"))
    except OSError:
        return []
    return [path for _,path in sorted(devices)]


def camera_probe(device):
    """Return V4L2 info only for real video-capture nodes, never metadata-only nodes."""
    try:
        result=subprocess.run(
            ["v4l2-ctl","-d",device,"--all"],
            check=False,
            capture_output=True,
            text=True,
            timeout=2
        )
    except (OSError,subprocess.SubprocessError):
        return None

    if result.returncode != 0:
        return None

    text=(result.stdout or "")+(result.stderr or "")

    # Inspect Device Caps specifically. The Arducam exposes /dev/video1 as
    # Metadata Capture; its broader Capabilities list also mentions video.
    # Looking only for the phrase "Video Capture" anywhere can therefore
    # select the wrong node.
    marker="Device Caps"
    if marker not in text:
        return None
    caps=text.split(marker,1)[1]
    for stop in ("Media Driver Info:","Interface Info:","Entity Info:"):
        if stop in caps:
            caps=caps.split(stop,1)[0]
            break
    if "Video Capture" not in caps:
        return None

    return text


def find_camera():
    """Prefer the known Arducam capture node, then any valid V4L2 capture node."""
    valid=[]
    for device in video_devices():
        info=camera_probe(device)
        if info is None:
            continue
        score=0
        if PREFERRED_CAMERA_TEXT in info:
            score+=10
        if PREFERRED_CAMERA_SERIAL and PREFERRED_CAMERA_SERIAL in info:
            score+=100
        valid.append((score,device))

    if not valid:
        return None

    # Highest identity score wins; lower /dev/videoN wins ties.
    valid.sort(key=lambda item:(-item[0],int(item[1].replace("/dev/video",""))))
    return valid[0][1]


def clipboard_copy_png(path):
    session=os.environ.get("XDG_SESSION_TYPE","").lower()

    if session=="wayland" and shutil.which("wl-copy"):
        with open(path,"rb") as f:
            subprocess.run(["wl-copy","--type","image/png"],stdin=f,check=False)
        return True

    if shutil.which("xclip"):
        subprocess.run(["xclip","-selection","clipboard","-t","image/png","-i",path],check=False)
        return True

    if shutil.which("wl-copy"):
        with open(path,"rb") as f:
            subprocess.run(["wl-copy","--type","image/png"],stdin=f,check=False)
        return True

    return False


def run_v4l2(args, capture=False):
    if not CAMERA:
        return subprocess.CompletedProcess([],1,"","")
    return subprocess.run(
        ["v4l2-ctl","-d",CAMERA]+args,
        check=False,
        capture_output=capture,
        text=capture
    )


def set_ctrl(name,value):
    result=run_v4l2(["--set-ctrl",f"{name}={int(value)}"],capture=True)
    return result.returncode == 0


def get_ctrl(name):
    result=run_v4l2(["--get-ctrl",name],capture=True)
    if result.returncode != 0:
        return None
    text=(result.stdout or "").strip()
    try:
        return int(text.rsplit(":",1)[1].strip())
    except (IndexError,ValueError):
        return None


def adjust_ctrl(name,delta,minimum,maximum,label):
    value=get_ctrl(name)
    if value is None:
        set_status(f"{label} unavailable",False)
        return
    value=max(minimum,min(maximum,value+delta))
    if not set_ctrl(name,value):
        set_status(f"Could not set {label}",False)
        return
    actual=get_ctrl(name)
    set_status(f"{label}: {actual if actual is not None else value}",True)


def connect_camera():
    global cap,CAMERA
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass

    cap=None
    CAMERA=find_camera()
    if not CAMERA:
        return False

    cap=cv2.VideoCapture(CAMERA,cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,FPS)

    if not cap.isOpened():
        try: cap.release()
        except Exception: pass
        cap=None
        return False

    # Opening is not enough: prove this node actually produces a frame.
    # This protects against virtual/metadata nodes that may open but are not
    # usable as the SkyCam image stream.
    for _ in range(5):
        try:
            ok,_frame=cap.read()
        except Exception:
            ok=False
        if ok:
            return True
        time.sleep(0.05)

    try: cap.release()
    except Exception: pass
    cap=None
    return False


root=tk.Tk()
root.title("🌸 SkyCam — Arducam 8MP")
root.geometry("1000x760")
root.minsize(900,650)
root.configure(bg=BG)

# Camera canvas takes every spare pixel. Controls live in a fixed dock.
root.grid_rowconfigure(0,weight=1)
root.grid_rowconfigure(1,weight=0,minsize=154)
root.grid_columnconfigure(0,weight=1)

video=tk.Canvas(root,bg=BG,highlightthickness=0,bd=0)
video.grid(row=0,column=0,sticky="nsew",padx=6,pady=(6,2))

dock=tk.Frame(root,bg=BG,height=154)
dock.grid(row=1,column=0,sticky="ew",padx=6,pady=(2,6))
dock.grid_propagate(False)
dock.grid_columnconfigure(0,weight=1)
for r in range(4):
    dock.grid_rowconfigure(r,weight=0)

status=tk.Label(dock,text="Starting SkyCam...",font=("Arial",10,"bold"),bg=BG,fg=WARN,
                anchor="w",padx=8,pady=2,height=1)
status.grid(row=0,column=0,sticky="ew",pady=(0,2))

bar1=tk.Frame(dock,bg=BG,height=38)
bar2=tk.Frame(dock,bg=BG,height=38)
bar3=tk.Frame(dock,bg=BG,height=38)
for bar,row in ((bar1,1),(bar2,2),(bar3,3)):
    bar.grid(row=row,column=0,sticky="ew",pady=1)
    bar.grid_propagate(False)
    bar.grid_rowconfigure(0,weight=1)


def setup_equal_columns(frame,count):
    for col in range(count):
        frame.grid_columnconfigure(col,weight=1,uniform=f"{id(frame)}cols")


def button(parent,text,command,column):
    b=tk.Button(parent,text=text,font=("Arial",9,"bold"),command=command,
                bg=BTN_BG,fg=FG,activebackground=ACTIVE,activeforeground=FG,
                relief="flat",bd=0,padx=2,pady=2)
    b.grid(row=0,column=column,sticky="nsew",padx=2,pady=1)
    return b


def process(frame):
    global rotation,digital_zoom
    if rotation==90: frame=cv2.rotate(frame,cv2.ROTATE_90_CLOCKWISE)
    elif rotation==180: frame=cv2.rotate(frame,cv2.ROTATE_180)
    elif rotation==270: frame=cv2.rotate(frame,cv2.ROTATE_90_COUNTERCLOCKWISE)

    if digital_zoom>1.0:
        h,w=frame.shape[:2]
        nw,nh=int(w/digital_zoom),int(h/digital_zoom)
        x1,y1=(w-nw)//2,(h-nh)//2
        frame=frame[y1:y1+nh,x1:x1+nw]
    return frame


def copy_image():
    if last_frame is None:
        set_status("No frame to copy",False); return
    tmp=tempfile.NamedTemporaryFile(delete=False,suffix=".png")
    tmp.close()
    cv2.imwrite(tmp.name,last_frame)
    ok=clipboard_copy_png(tmp.name)
    os.unlink(tmp.name)
    set_status("Copied image to clipboard 📋" if ok else "Clipboard tool missing",ok)


def save_image():
    if last_frame is None:
        set_status("No frame to save",False); return
    name=time.strftime("skycam_%Y-%m-%d_%H-%M-%S.png")
    path=os.path.join(CAPTURES,name)
    cv2.imwrite(path,last_frame)
    set_status(f"Saved: {name}",True)


def refresh_camera():
    if connect_camera():
        set_status(f"Camera refreshed ✓ {CAMERA}",True)
    else:
        set_status("Camera not found",False)


def rotate_image():
    global rotation
    rotation=(rotation+90)%360
    set_status(f"Rotation: {rotation}°",True)


def zoom_in():
    global digital_zoom
    digital_zoom=min(digital_zoom+0.25,4.0)
    set_status(f"Digital zoom: {digital_zoom:.2f}x",True)


def zoom_out():
    global digital_zoom
    digital_zoom=max(digital_zoom-0.25,1.0)
    set_status(f"Digital zoom: {digital_zoom:.2f}x",True)


def pin_toggle():
    current=bool(root.attributes("-topmost"))
    root.attributes("-topmost",not current)
    set_status("Pinned on top 📌" if not current else "Unpinned",True)


def normal_preset():
    # Arducam-reported defaults from this camera.
    set_ctrl("auto_exposure",3)
    set_ctrl("brightness",128)
    set_ctrl("contrast",34)
    set_ctrl("sharpness",38)
    set_ctrl("gain",0)
    set_ctrl("white_balance_automatic",1)
    set_ctrl("power_line_frequency",2)
    set_status("NORMAL preset — camera defaults + 60 Hz",True)


def pcb_preset():
    # Conservative bench preset: preserve auto exposure, add contrast/detail,
    # avoid electronic gain noise, and use US 60 Hz anti-flicker.
    set_ctrl("auto_exposure",3)
    set_ctrl("brightness",128)
    set_ctrl("contrast",55)
    set_ctrl("sharpness",90)
    set_ctrl("gain",0)
    set_ctrl("white_balance_automatic",1)
    set_ctrl("power_line_frequency",2)
    set_status("PCB preset — contrast 55 | sharpness 90 | gain 0",True)


def brightness_down(): adjust_ctrl("brightness",-5,0,255,"Brightness")
def brightness_up(): adjust_ctrl("brightness",5,0,255,"Brightness")
def contrast_down(): adjust_ctrl("contrast",-5,0,255,"Contrast")
def contrast_up(): adjust_ctrl("contrast",5,0,255,"Contrast")
def sharpness_down(): adjust_ctrl("sharpness",-10,0,255,"Sharpness")
def sharpness_up(): adjust_ctrl("sharpness",10,0,255,"Sharpness")
def gain_down(): adjust_ctrl("gain",-5,0,255,"Gain")
def gain_up(): adjust_ctrl("gain",5,0,255,"Gain")


def exposure_auto():
    if set_ctrl("auto_exposure",3):
        set_status("Exposure: AUTO",True)
    else:
        set_status("Could not enable auto exposure",False)


def exposure_adjust(delta):
    # exposure_time_absolute is inactive until Manual Mode is selected.
    set_ctrl("auto_exposure",1)
    value=get_ctrl("exposure_time_absolute")
    if value is None:
        set_status("Manual exposure unavailable",False)
        return
    value=max(3,min(2047,value+delta))
    if set_ctrl("exposure_time_absolute",value):
        actual=get_ctrl("exposure_time_absolute")
        set_status(f"Exposure MANUAL: {actual if actual is not None else value}",True)
    else:
        set_status("Could not set manual exposure",False)


def exposure_down(): exposure_adjust(-20)
def exposure_up(): exposure_adjust(20)


def camera_info():
    values=[]
    if CAMERA:
        values.append(CAMERA)
    for label,name in (("B","brightness"),("C","contrast"),("S","sharpness"),("G","gain")):
        value=get_ctrl(name)
        if value is not None:
            values.append(f"{label}:{value}")
    ae=get_ctrl("auto_exposure")
    values.append("EXP:AUTO" if ae==3 else "EXP:MAN")
    set_status(" | ".join(values),True)


setup_equal_columns(bar1,7)
button(bar1,"COPY",copy_image,0)
button(bar1,"SAVE",save_image,1)
button(bar1,"REFRESH",refresh_camera,2)
button(bar1,"ROTATE",rotate_image,3)
button(bar1,"ZOOM +",zoom_in,4)
button(bar1,"ZOOM -",zoom_out,5)
button(bar1,"PIN",pin_toggle,6)

setup_equal_columns(bar2,8)
button(bar2,"PCB",pcb_preset,0)
button(bar2,"NORMAL",normal_preset,1)
button(bar2,"BRIGHT -",brightness_down,2)
button(bar2,"BRIGHT +",brightness_up,3)
button(bar2,"CONTRAST -",contrast_down,4)
button(bar2,"CONTRAST +",contrast_up,5)
button(bar2,"SHARP -",sharpness_down,6)
button(bar2,"SHARP +",sharpness_up,7)

setup_equal_columns(bar3,7)
button(bar3,"EXP AUTO",exposure_auto,0)
button(bar3,"EXP -",exposure_down,1)
button(bar3,"EXP +",exposure_up,2)
button(bar3,"GAIN -",gain_down,3)
button(bar3,"GAIN +",gain_up,4)
button(bar3,"INFO",camera_info,5)
button(bar3,"RESET",normal_preset,6)


def render_to_canvas(frame):
    global video_photo,video_item
    cw=max(video.winfo_width(),1)
    ch=max(video.winfo_height(),1)
    if cw<32 or ch<32:
        return

    h,w=frame.shape[:2]
    scale=min(cw/w,ch/h)
    out_w=max(1,int(w*scale))
    out_h=max(1,int(h*scale))
    interpolation=cv2.INTER_AREA if scale<1.0 else cv2.INTER_CUBIC
    display=cv2.resize(frame,(out_w,out_h),interpolation=interpolation)
    display=cv2.cvtColor(display,cv2.COLOR_BGR2RGB)
    video_photo=ImageTk.PhotoImage(Image.fromarray(display))

    x=cw//2
    y=ch//2
    if video_item is None:
        video_item=video.create_image(x,y,image=video_photo,anchor="center")
    else:
        video.coords(video_item,x,y)
        video.itemconfigure(video_item,image=video_photo)


def update_frame():
    global cap,last_frame
    ret=False; frame=None
    if cap is not None:
        try: ret,frame=cap.read()
        except Exception: ret=False

    if not ret:
        set_status("Searching for camera...",False)
        if connect_camera(): set_status(f"Camera reconnected ✓ {CAMERA}",True)
        root.after(1000,update_frame)
        return

    frame=process(frame)
    last_frame=frame.copy()
    render_to_canvas(frame)
    root.after(20,update_frame)


def close():
    try:
        if cap is not None: cap.release()
    except Exception:
        pass
    root.destroy()


connect_camera()
root.protocol("WM_DELETE_WINDOW",close)
update_frame()
root.mainloop()
