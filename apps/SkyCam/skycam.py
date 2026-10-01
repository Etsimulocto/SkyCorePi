# skycam.py
# run with: python3 ~/SkyCam/skycam.py
# path: /home/quarterbitgames/SkyCam/skycam.py
# description: BloomCore SkyCam. Auto camera reconnect. Clipboard works on X11 or Wayland.
# version: 1.4
# format: bloomcore/v1.3

import cv2, subprocess, tempfile, os, time, shutil, tkinter as tk
from PIL import Image, ImageTk

BASE=os.path.expanduser("~/SkyCam")
CAPTURES=os.path.join(BASE,"captures")
os.makedirs(CAPTURES,exist_ok=True)

CAMERA="/dev/video0"
WIDTH,HEIGHT,FPS=1280,720,30

BG="#050505"; FG="#ffffff"; BTN_BG="#1b1b1b"; ACTIVE="#333333"
GOOD="#7CFF7C"; WARN="#FFD36A"

cap=None
last_frame=None
rotation=0
digital_zoom=1.0
video_photo=None
video_item=None

# Most UVC autofocus webcams expose focus_absolute on a 0..255 scale.
# Lower values are nearer focus on the camera currently used with SkyCam.
FOCUS_MIN=0
FOCUS_MAX=255
FOCUS_STEP=10
FOCUS_FINE_STEP=2
PCB_COARSE_STEP=20
PCB_FINE_RADIUS=18
PCB_FINE_STEP=2
focus_value=None
pcb_scan_running=False


def set_status(text, good=True):
    status.config(text=text, fg=GOOD if good else WARN)


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
    return subprocess.run(
        ["v4l2-ctl","-d",CAMERA]+args,
        check=False,
        capture_output=capture,
        text=capture
    )


def set_ctrl(name,value):
    run_v4l2(["--set-ctrl",f"{name}={value}"])


def get_ctrl(name):
    result=run_v4l2(["--get-ctrl",name],capture=True)
    if result.returncode != 0:
        return None
    text=(result.stdout or "").strip()
    try:
        return int(text.rsplit(":",1)[1].strip())
    except (IndexError,ValueError):
        return None


def sync_focus():
    global focus_value
    current=get_ctrl("focus_absolute")
    if current is not None:
        focus_value=max(FOCUS_MIN,min(FOCUS_MAX,current))
    elif focus_value is None:
        focus_value=(FOCUS_MIN+FOCUS_MAX)//2
    return focus_value


def connect_camera():
    global cap,focus_value
    try:
        if cap is not None:
            cap.release()
    except Exception:
        pass

    cap=cv2.VideoCapture(CAMERA,cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FOURCC,cv2.VideoWriter_fourcc(*"MJPG"))
    cap.set(cv2.CAP_PROP_FRAME_WIDTH,WIDTH)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT,HEIGHT)
    cap.set(cv2.CAP_PROP_FPS,FPS)
    opened=cap.isOpened()
    if opened:
        focus_value=None
        sync_focus()
    return opened


root=tk.Tk()
root.title("🌸 SkyCam")
root.geometry("960x680")
root.minsize(760,520)
root.configure(bg=BG)

# The canvas owns all flexible space. A Canvas does not request the size of
# the displayed camera frame, so the camera image can no longer resize the
# application window or push the controls off-screen.
root.grid_rowconfigure(0,weight=1)
for row in (1,2,3,4):
    root.grid_rowconfigure(row,weight=0)
root.grid_columnconfigure(0,weight=1)

video=tk.Canvas(root,bg=BG,highlightthickness=0,bd=0)
video.grid(row=0,column=0,sticky="nsew",padx=6,pady=(6,2))

status=tk.Label(root,text="Starting SkyCam...",font=("Arial",10,"bold"),bg=BG,fg=WARN,
                anchor="w",padx=8,pady=3)
status.grid(row=1,column=0,sticky="ew",padx=6,pady=(1,1))

bar1=tk.Frame(root,bg=BG,height=36)
bar2=tk.Frame(root,bg=BG,height=36)
bar3=tk.Frame(root,bg=BG,height=36)
for bar in (bar1,bar2,bar3):
    bar.grid_propagate(False)
bar1.grid(row=2,column=0,sticky="ew",padx=6,pady=1)
bar2.grid(row=3,column=0,sticky="ew",padx=6,pady=1)
bar3.grid(row=4,column=0,sticky="ew",padx=6,pady=(1,5))


def setup_equal_columns(frame,count):
    for col in range(count):
        frame.grid_columnconfigure(col,weight=1,uniform=f"{id(frame)}cols")
    frame.grid_rowconfigure(0,weight=1)


def button(parent,text,command,column):
    b=tk.Button(parent,text=text,font=("Arial",9,"bold"),command=command,
                bg=BTN_BG,fg=FG,activebackground=ACTIVE,activeforeground=FG,
                relief="flat",bd=0,padx=3,pady=3)
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
    set_status("Camera refreshed ✓",True) if connect_camera() else set_status("Camera not found",False)


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


def focus_auto():
    global focus_value
    set_ctrl("focus_automatic_continuous",1)
    focus_value=None
    set_status("Autofocus ON 🎯",True)


def manual_focus_delta(delta,label):
    global focus_value
    sync_focus()
    set_ctrl("focus_automatic_continuous",0)
    focus_value=max(FOCUS_MIN,min(FOCUS_MAX,focus_value+delta))
    set_ctrl("focus_absolute",focus_value)
    actual=get_ctrl("focus_absolute")
    if actual is not None:
        focus_value=actual
    set_status(f"{label}: {focus_value}",True)


def focus_near():
    manual_focus_delta(-FOCUS_STEP,"Focus near")


def focus_far():
    manual_focus_delta(FOCUS_STEP,"Focus far")


def focus_near_fine():
    manual_focus_delta(-FOCUS_FINE_STEP,"Fine near")


def focus_far_fine():
    manual_focus_delta(FOCUS_FINE_STEP,"Fine far")


def focus_macro():
    global focus_value
    set_ctrl("focus_automatic_continuous",0)
    focus_value=FOCUS_MIN
    set_ctrl("focus_absolute",focus_value)
    actual=get_ctrl("focus_absolute")
    if actual is not None:
        focus_value=actual
    set_status(f"PCB / MACRO focus: {focus_value} — use fine focus if needed",True)


def focus_read():
    value=sync_focus()
    set_status(f"Current focus: {value}",True)


def sharpness_score(frame):
    if frame is None:
        return -1.0
    h,w=frame.shape[:2]
    x1,x2=int(w*0.20),int(w*0.80)
    y1,y2=int(h*0.20),int(h*0.80)
    roi=frame[y1:y2,x1:x2]
    gray=cv2.cvtColor(roi,cv2.COLOR_BGR2GRAY)
    return float(cv2.Laplacian(gray,cv2.CV_64F).var())


def grab_focus_frame(settle_frames=3):
    frame=None
    if cap is None:
        return None
    for _ in range(settle_frames):
        ok,frame=cap.read()
        if not ok:
            return None
    return frame


def pcb_autofocus():
    global focus_value,pcb_scan_running
    if pcb_scan_running:
        return
    if cap is None or not cap.isOpened():
        set_status("Camera not ready",False)
        return

    pcb_scan_running=True
    set_ctrl("focus_automatic_continuous",0)
    set_status("PCB AUTO: scanning focus...",True)
    root.update_idletasks()

    best_value=None
    best_score=-1.0

    for value in range(FOCUS_MIN,FOCUS_MAX+1,PCB_COARSE_STEP):
        set_ctrl("focus_absolute",value)
        time.sleep(0.04)
        frame=grab_focus_frame(3)
        score=sharpness_score(frame)
        if score>best_score:
            best_score=score
            best_value=value

    if best_value is None:
        pcb_scan_running=False
        set_status("PCB AUTO could not read a sharp frame",False)
        return

    fine_start=max(FOCUS_MIN,best_value-PCB_FINE_RADIUS)
    fine_end=min(FOCUS_MAX,best_value+PCB_FINE_RADIUS)
    for value in range(fine_start,fine_end+1,PCB_FINE_STEP):
        set_ctrl("focus_absolute",value)
        time.sleep(0.03)
        frame=grab_focus_frame(2)
        score=sharpness_score(frame)
        if score>best_score:
            best_score=score
            best_value=value

    set_ctrl("focus_absolute",best_value)
    time.sleep(0.05)
    actual=get_ctrl("focus_absolute")
    focus_value=actual if actual is not None else best_value
    pcb_scan_running=False
    set_status(f"PCB AUTO locked focus: {focus_value} | sharpness {best_score:.0f}",True)


setup_equal_columns(bar1,7)
button(bar1,"COPY",copy_image,0)
button(bar1,"SAVE",save_image,1)
button(bar1,"REFRESH",refresh_camera,2)
button(bar1,"ROTATE",rotate_image,3)
button(bar1,"ZOOM +",zoom_in,4)
button(bar1,"ZOOM -",zoom_out,5)
button(bar1,"PIN",pin_toggle,6)

setup_equal_columns(bar2,5)
button(bar2,"AUTO FOCUS",focus_auto,0)
button(bar2,"PCB AUTO",pcb_autofocus,1)
button(bar2,"MACRO",focus_macro,2)
button(bar2,"NEAR",focus_near,3)
button(bar2,"FAR",focus_far,4)

setup_equal_columns(bar3,3)
button(bar3,"FINE <",focus_near_fine,0)
button(bar3,"FOCUS #",focus_read,1)
button(bar3,"FINE >",focus_far_fine,2)


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
    if pcb_scan_running:
        root.after(50,update_frame)
        return

    ret=False; frame=None
    if cap is not None:
        try: ret,frame=cap.read()
        except Exception: ret=False

    if not ret:
        set_status("Searching for camera...",False)
        if connect_camera(): set_status("Camera reconnected ✓",True)
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
