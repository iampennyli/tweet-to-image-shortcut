# v14 style table: colors copied from /workspace/tweet-mockups/src/build.py (TH), backgrounds as small embedded PNGs
import base64,io,math,zlib
from PIL import Image
def hx(c): return tuple(int(c[i:i+2],16) for i in (1,3,5))
def grad(stops,w=36,h=48,deg=160):
    # CSS linear-gradient(deg) sampled on a w x h image (aspect of the 1080x1440 page)
    im=Image.new('RGB',(w,h)); a=math.radians(deg); dx,dy=math.sin(a),-math.cos(a)
    L=abs(w*dx)+abs(h*dy)
    for y in range(h):
        for x in range(w):
            t=((x+.5-w/2)*dx+(y+.5-h/2)*dy)/L+.5; t=min(1,max(0,t))
            for i in range(len(stops)-1):
                (p0,c0),(p1,c1)=stops[i],stops[i+1]
                if t<=p1 or i==len(stops)-2:
                    f=0 if p1==p0 else min(1,max(0,(t-p0)/(p1-p0)))
                    im.putpixel((x,y),tuple(round(hx(c0)[k]+(hx(c1)[k]-hx(c0)[k])*f) for k in range(3))); break
    return im
def b64png(im):
    b64png.best=(10**9,None)
    # pick an encoding whose base64 has no '+' (avoid '+' in Text/Dictionary literals)
    for lvl in (9,):
        for q in (None,):
            bio=io.BytesIO(); im.save(bio,'PNG',compress_level=lvl,optimize=False); s=base64.b64encode(bio.getvalue()).decode()
            if '+' not in s: return s
    import random; rnd=random.Random(7)
    for n in range(200000):   # nudge ONE pixel channel by 1 (invisible) at a time until the base64 has no '+'
        j=im.copy(); x,y=rnd.randrange(im.width),rnd.randrange(im.height); p=list(j.getpixel((x,y))); c=rnd.randrange(3)
        p[c]=p[c]+1 if p[c]<255 else p[c]-1; j.putpixel((x,y),tuple(p))
        bio=io.BytesIO(); j.save(bio,'PNG',compress_level=9); s=base64.b64encode(bio.getvalue()).decode()
        if '+' not in s: return s
        if s.count('+')<=b64png.best[0]: b64png.best=(s.count('+'),j); im=j   # greedy: keep changes that don't add '+'
    raise SystemExit('no plus-free encoding')
TH={
 'light':dict(stops=[(0,'#e0ecff'),(.55,'#f3e8ff'),(1,'#ffe9f0')],CARD='#ffffff',FG='#0f1419',SUB='#536471',TRC='#7a8a99',LINE='#e6ecf0',PH='#f5f8fa'),
 'dark': dict(stops=[(0,'#0f172a'),(.55,'#1e1b4b'),(1,'#312e81')],CARD='#15202b',FG='#e7e9ea',SUB='#8b98a5',TRC='#8794a6',LINE='#2f3b47',PH='#1e2a36'),
 'paper':dict(stops=[(0,'#f6efe3'),(1,'#efe2cc')],CARD='#fffaf1',FG='#3b2f25',SUB='#8a7560',TRC='#a08b74',LINE='#e6d8c0',PH='#f6eddd'),
}
LABEL={'light':'浅色','dark':'深色','paper':'纸感'}
KEYS=['PAGEBG','CARDBG','CARD','FG','SUB','TRC','LINE','PH','HTMLBG']
def style(name):
    t=TH[name]; d={k:t[k] for k in ('CARD','FG','SUB','TRC','LINE','PH')}
    d['PAGEBG']=b64png(grad(t['stops'])); d['CARDBG']=b64png(Image.new('RGB',(4,4),hx(t['CARD']))); d['HTMLBG']=t['stops'][0][1]
    return d
STYLES={k:style(k) for k in TH}
