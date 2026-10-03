"""Lightweight local face/motion targets; no identity recognition or chat vision."""
import glob
from pathlib import Path
import time


def choose_target(boxes,previous=None):
    if not len(boxes):return None
    if previous is None:return max(boxes,key=lambda b:int(b[2])*int(b[3]))
    px,py=previous
    return min(boxes,key=lambda b:(b[0]+b[2]/2-px)**2+(b[1]+b[3]/2-py)**2)


def normalized_center(box,width,height):
    x,y,w,h=box
    return max(-1,min(1,(x+w/2)/width*2-1)),max(-1,min(1,(y+h/2)/height*2-1))

class Tracker:
    def __init__(self,cv):
        self.cv=cv;self.mode=0;self.detector=None;self.background=None;self.previous=None;self.boxes=[];self.target=None;self.last=0;self.error='';self.hands=None;self.gesture=None;self.confidence=0;self.points=[]
    def reset(self,mode):
        self.mode=mode;self.background=None;self.previous=None;self.boxes=[];self.target=None;self.last=0;self.error=''
        self.gesture=None;self.confidence=0;self.points=[]
        if mode==3 and self.hands is None:
            try:
                from gestures import HandRecognizer
                self.hands=HandRecognizer()
            except Exception as exc:self.error='Hands unavailable: '+str(exc)
        if mode==1 and self.detector is None:
            paths=[]
            if hasattr(self.cv,'data'):paths.append(str(Path(self.cv.data.haarcascades)/'haarcascade_frontalface_default.xml'))
            paths+=glob.glob('/usr/share/opencv*/haarcascades/haarcascade_frontalface_default.xml')
            path=next((p for p in paths if Path(p).is_file()),None)
            if not path:self.error='Face data missing: install opencv-data';return
            self.detector=self.cv.CascadeClassifier(path)
            if self.detector.empty():self.error='Face detector could not load';self.detector=None
    def process(self,frame,mode,overlay=True):
        cv=self.cv
        if mode!=self.mode:self.reset(mode)
        started=time.monotonic()
        if mode and started-self.last>=0.2:
            self.last=started
            gray=cv.cvtColor(frame,cv.COLOR_BGR2GRAY)
            if mode==1 and self.detector is not None:
                self.boxes=list(self.detector.detectMultiScale(gray,scaleFactor=1.15,minNeighbors=5,minSize=(28,28)))
            elif mode==2:
                gray=cv.GaussianBlur(gray,(7,7),0)
                if self.background is None:self.background=gray.astype('float')
                difference=cv.absdiff(gray,cv.convertScaleAbs(self.background))
                mask=cv.threshold(difference,25,255,cv.THRESH_BINARY)[1]
                mask=cv.dilate(mask,None,iterations=2)
                contours=cv.findContours(mask,cv.RETR_EXTERNAL,cv.CHAIN_APPROX_SIMPLE)[-2]
                self.boxes=[cv.boundingRect(c) for c in contours if cv.contourArea(c)>350]
                cv.accumulateWeighted(gray,self.background,0.08)
            elif mode==3 and self.hands is not None:
                try:
                    self.gesture,self.confidence,self.points=self.hands.detect(cv.cvtColor(frame,cv.COLOR_BGR2RGB))
                    if self.points:
                        h,w=frame.shape[:2];xs=[p[0]*w for p in self.points];ys=[p[1]*h for p in self.points]
                        self.boxes=[(min(xs),min(ys),max(xs)-min(xs),max(ys)-min(ys))]
                    else:self.boxes=[]
                except Exception as exc:
                    self.error='Hand recognition error: '+str(exc);self.boxes=[];self.gesture=None;self.confidence=0
            box=choose_target(self.boxes,self.previous)
            if box is not None:
                x,y,w,h=map(int,box);self.previous=(x+w/2,y+h/2);self.target=normalized_center(box,frame.shape[1],frame.shape[0])
            else:self.target=None;self.previous=None
            result={'target':self.target,'count':len(self.boxes),'mode':mode,'ms':round((time.monotonic()-started)*1000,1),'error':self.error,'gesture':self.gesture,'confidence':self.confidence}
        else:result=None
        if overlay and mode:
            h,w=frame.shape[:2]
            for px,py in self.points:cv.circle(frame,(int(px*w),int(py*h)),2,(0,200,255),-1)
            for box in self.boxes:
                x,y,w,h=map(int,box);cv.rectangle(frame,(x,y),(x+w,y+h),(0,230,180),1)
            if self.target:
                h,w=frame.shape[:2];cx=int((self.target[0]+1)*w/2);cy=int((self.target[1]+1)*h/2)
                cv.drawMarker(frame,(cx,cy),(255,100,20),cv.MARKER_CROSS,12,1)
        return result

    def close(self):
        if self.hands is not None:self.hands.close();self.hands=None
