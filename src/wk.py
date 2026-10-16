import sys,re
from playwright.sync_api import sync_playwright
from PIL import Image
html,out=sys.argv[1],sys.argv[2]
H=int(re.search(r'@page\{size:1080px (\d+)px',open(html).read()).group(1))
with sync_playwright() as p:
    b=p.webkit.launch(); pg=b.new_page(viewport={'width':1080,'height':H})
    pg.goto('file://'+__import__('os').path.abspath(html)); pg.emulate_media(media='print')
    pg.screenshot(path=out,full_page=True); b.close()
im=Image.open(out).convert('L');w,h=im.size;ys=[y for y in range(h) if im.getpixel((100,y))>=254]
print(out,'H',H,'img',h,'top',ys[0],'bottom',h-1-ys[-1])
