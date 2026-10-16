import json,html,base64,urllib.request,datetime,re,sys,math
src=sys.argv[1] if len(sys.argv)>1 else 'data.json'; out=sys.argv[2] if len(sys.argv)>2 else 'filled.html'
dup=int(sys.argv[3]) if len(sys.argv)>3 else 0
ph_override=None
t=json.load(open(src))['tweet'];a=t['author']
def k(n):
  n=n or 0
  return f"{n/10000:.1f}万".replace('.0万','万') if n>=10000 else str(n)
def b64(u):
  d=urllib.request.urlopen(urllib.request.Request(u,headers={'User-Agent':'curl/8'}),timeout=20).read();return 'data:image/jpeg;base64,'+base64.b64encode(d).decode()
CJK=r'[\u2e80-\u9fff\u3000-\u303f\uac00-\ud7af\uff00-\uffef]'
def estimate(text,tr):
  # SAME formula as the shortcut's 计算 expression
  c1=len(re.findall(CJK,text)); n1=text.count('\n'); l1=len(text)-c1
  c2=len(re.findall(CJK,tr)); n2=tr.count('\n'); l2=len(tr)-c2
  h=0.965*(680+(c1/17+l1/36+n1+1)*68.2+(c2/24+l2/50+n2+1)*50.7+(60 if tr else 0))
  return max(1440,round(h+MH))
med=t.get('media') or {}
items=[(p['url'],p['width'],p['height'],'m') for p in (med.get('photos') or [])]+[(v['thumbnail_url'],v['width'],v['height'],'m v') for v in (med.get('videos') or [])]
if dup: items=(items*4)[:dup]   # synthetic 3/4-tile test
frags=[];first_h=0
for u,w,h,c in items:
  hh=min(1200,round(796*h/w)); first_h=hh
  frags.append(f'<div class="{c}" style="--h:{hh}px"><img src="{b64(re.sub(r"[?].*$","",u)+"?name=medium")}" /></div>')
N=len(frags); MH=0 if N==0 else first_h+40 if N==1 else 460 if N==2 else 812
tr=((t.get('translation') or {}).get('text') or '').strip()
H0=estimate(t['text'],tr)
pages=math.ceil(H0/1397.6); SL=(pages-1)*40 if H0>1440 else 0; H=H0+SL
ph=((t.get('media') or {}).get('photos') or [{}])[0].get('url','')
dt=datetime.datetime.strptime(t['created_at'],'%a %b %d %H:%M:%S %z %Y').astimezone(datetime.timezone(datetime.timedelta(hours=8)))
v={'TEXT':html.escape(t['text']),'TRANSLATION':html.escape(tr),'NAME':html.escape(a['name']),'HANDLE':html.escape(a['screen_name']),
'AVATAR':b64(a['avatar_url']),'PHOTO':'','PHOTO_DISPLAY':'none',
'LIKES':k(t['likes']),'RETWEETS':k(t['retweets']),'REPLIES':k(t['replies']),'VIEWS':k(t.get('views')),
'DATE':dt.strftime('%Y年%-m月%-d日 %H:%M'),'FONT_SIZE':'44','MEDIA':' '.join(frags),'MEDIA_COUNT':str(N),'PAGE_HEIGHT':str(H),'PAD_BOTTOM':str(60+SL),'PAD_TOP':'60' if H0>1440 else '103','BODY_HEIGHT':str(H) if H0>1440 else '1397'}
s=open('template.html').read()
for x,y in v.items(): s=s.replace('{{'+x+'}}',y)
s=s.replace('</body>','<script>document.body.dataset.need=document.querySelector(".card").offsetHeight+120+"_"+document.querySelector(".card").getBoundingClientRect().top</script></body>')
open(out,'w').write(s);print("estimate",H)
