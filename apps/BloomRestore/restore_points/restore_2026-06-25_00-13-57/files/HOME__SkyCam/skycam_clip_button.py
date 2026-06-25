import cv2, subprocess, tempfile, os, tkinter as tk
from PIL import Image, ImageTk

CAMERA="/dev/video0"
WIDTH, HEIGHT, FPS = 1280, 720, 30
rotation = 0
last_frame = None

cap = cv2.VideoCapture(CAMERA, cv2.CAP_V4L2)
cap.set(cv2.CAP_PROP_FOURCC, cv2.VideoWriter_fourcc(*"MJPG"))
cap.set(cv2.CAP_PROP_FRAME_WIDTH, WIDTH)
cap.set(cv2.CAP_PROP_FRAME_HEIGHT, HEIGHT)
cap.set(cv2.CAP_PROP_FPS, FPS)

root = tk.Tk()
root.title("SkyCam")
root.geometry("900x620")
root.minsize(420, 330)

video = tk.Label(root, bg="black")
video.pack(fill="both", expand=True)

status = tk.Label(root, text="SkyCam ready", font=("Arial", 11))
status.pack(fill="x")

def apply_rotation(frame):
    if rotation == 90:
        return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
    if rotation == 180:
        return cv2.rotate(frame, cv2.ROTATE_180)
    if rotation == 270:
        return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
    return frame

def copy_image():
    global last_frame
    if last_frame is None:
        status.config(text="No frame yet")
        return
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".png")
    tmp.close()
    cv2.imwrite(tmp.name, last_frame)
    with open(tmp.name, "rb") as f:
        subprocess.run(["wl-copy", "--type", "image/png"], stdin=f)
    os.unlink(tmp.name)
    status.config(text="Copied image to clipboard 📋")

def rotate_image():
    global rotation
    rotation = (rotation + 90) % 360
    status.config(text=f"Rotation: {rotation}°")

def update_frame():
    global last_frame
    ret, frame = cap.read()
    if ret:
        frame = apply_rotation(frame)
        last_frame = frame.copy()

        vw, vh = max(video.winfo_width(), 320), max(video.winfo_height(), 240)
        h, w = frame.shape[:2]
        scale = min(vw / w, vh / h)
        display = cv2.resize(frame, (int(w * scale), int(h * scale)))
        display = cv2.cvtColor(display, cv2.COLOR_BGR2RGB)

        img = ImageTk.PhotoImage(Image.fromarray(display))
        video.imgtk = img
        video.config(image=img)

    root.after(20, update_frame)

bar = tk.Frame(root)
bar.pack(fill="x")

tk.Button(bar, text="📷 COPY IMAGE TO CLIPBOARD", font=("Arial", 15, "bold"), command=copy_image).pack(side="left", fill="x", expand=True)
tk.Button(bar, text="↻", font=("Arial", 18, "bold"), width=4, command=rotate_image).pack(side="right")

def close():
    cap.release()
    root.destroy()

root.protocol("WM_DELETE_WINDOW", close)
update_frame()
root.mainloop()
