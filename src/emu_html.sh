# emulate iOS Make PDF on an already-filled HTML: Letter pages, no margin, 1080px->page width, backgrounds dropped
# usage: emu_html.sh in.html out_stitched.png  -> prints stitched size and card top/bottom (cropping optional: $3=crop height)
set -e
cp $1 /tmp/e.html
sed -i -E 's/@page\{[^}]*\}//' /tmp/e.html
sed -i 's|</style>|@page{size:letter;margin:0} html{zoom:0.75556}</style>|' /tmp/e.html
google-chrome --headless=new --no-sandbox --disable-gpu --no-pdf-header-footer --print-to-pdf=/tmp/e.pdf file:///tmp/e.html 2>/dev/null   # no --print-background => CSS backgrounds dropped
rm -f /tmp/ep-*; pdftoppm -r 127.06 -png /tmp/e.pdf /tmp/ep
python3 - "$2" "${3:-0}" <<'PY'
import sys,glob
from PIL import Image
out,H=sys.argv[1],int(sys.argv[2])
ps=[Image.open(p).convert('RGB') for p in sorted(glob.glob('/tmp/ep-*.png'))]
W=1080; ps=[p.resize((W,round(p.height*W/p.width))) for p in ps]
st=Image.new('RGB',(W,sum(p.height for p in ps)),'white'); y=0
for p in ps: st.paste(p,(0,y)); y+=p.height
if H: st=st.crop((0,0,W,min(H,st.height)))
st.save(out)
g=st.convert('L'); ys=[y for y in range(st.height) if g.getpixel((540,y))<250 or g.getpixel((80,y))<250]
# card edges: find rows where x=60 (outside card) differs from x=540; simpler: report first/last non-bg row at x=75 (card left edge region)
col=[g.getpixel((75,y)) for y in range(st.height)]; bg=col[0]
rows=[y for y,v in enumerate(col) if abs(v-bg)>3]
print(out,'pages',len(ps),'size',st.size,'card-edge first',rows[0] if rows else None,'last-from-bottom',st.height-1-rows[-1] if rows else None)
PY
