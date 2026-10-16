import plistlib,re,uuid
A=[]
def ref(u,name): return {"Type":"ActionOutput","OutputUUID":u,"OutputName":name}
SI={"Type":"ExtensionInput"}
def att(r): return {"Value":r,"WFSerializationType":"WFTextTokenAttachment"}
def tok(parts):
    s="";a={}
    for p in parts:
        if isinstance(p,dict): a["{%d, 1}"%(len(s.encode('utf-16-le'))//2)]=p; s+="\ufffc"
        else: s+=p
    return {"Value":{"string":s,"attachmentsByRange":a},"WFSerializationType":"WFTextTokenString"}
def act(i,name=None,**p):
    u=str(uuid.uuid4()).upper()
    if name: p["UUID"]=u; p["CustomOutputName"]=name
    A.append({"WFWorkflowActionIdentifier":"is.workflow.actions."+i,"WFWorkflowActionParameters":p})
    return ref(u,name) if name else None
inp=act("gettext","输入文本",WFTextActionText=tok([SI]))
m=act("text.match","匹配",WFMatchTextPattern=r"(?:x|twitter)\.com/[^/?#]+/status/(\d+)",WFMatchTextCaseSensitive=False,text=tok([inp]))
g=act("text.match.getgroup","推文ID",WFGetGroupType="Group At Index",WFGroupIndex=1,matches=att(m))
gid=str(uuid.uuid4()).upper()
act("conditional",GroupingIdentifier=gid,WFControlFlowMode=0,WFCondition=101,WFInput={"Type":"Variable","Variable":att(g)})
act("alert",WFAlertActionTitle="没识别到推文链接",WFAlertActionMessage=tok(["收到的输入：\n",inp]),WFAlertActionCancelButtonShown=False)
act("exit")
act("conditional",GroupingIdentifier=gid,WFControlFlowMode=2)
url=act("url","API地址",WFURLActionURL=tok(["https://api.fxtwitter.com/status/",g,"/zh"]))
def endif(gid,name):
    u=str(uuid.uuid4()).upper()
    A.append({"WFWorkflowActionIdentifier":"is.workflow.actions.conditional","WFWorkflowActionParameters":{"GroupingIdentifier":gid,"WFControlFlowMode":2,"UUID":u}})
    return ref(u,"If Result")
def cond(c,x):
    gid=str(uuid.uuid4()).upper()
    act("conditional",GroupingIdentifier=gid,WFControlFlowMode=0,WFCondition=c,WFInput={"Type":"Variable","Variable":att(x)}); return gid
def other(gid): act("conditional",GroupingIdentifier=gid,WFControlFlowMode=1)
def fetch(tag):
    d=act("downloadurl","数据"+tag,WFURL=tok([url]),WFHTTPMethod="GET")
    t=act("getvalueforkey","推文"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey="tweet",WFInput=att(d))
    trd=act("getvalueforkey","翻译字典"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey="translation",WFInput=att(t))
    gid=cond(100,trd)
    x=act("getvalueforkey","译文原始"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey="text",WFInput=att(trd))
    act("gettext","译文值"+tag,WFTextActionText=tok([x]))
    other(gid); act("gettext","空译文"+tag,WFTextActionText="")
    return t,endif(gid,"If Result")
T,tr1=fetch("1")
gid=cond(101,tr1)
act("delay",WFDelayTime=2)
_,tr2=fetch("2")
act("gettext","重试译文",WFTextActionText=tok([tr2]))
other(gid); act("gettext","首次译文",WFTextActionText=tok([tr1]))
v={"译文":endif(gid,"If Result")}
au=act("getvalueforkey","作者",WFGetDictionaryValueType="Value",WFDictionaryKey="author",WFInput=att(T))
for src,k,n in [(T,"text","正文"),(au,"name","昵称"),(au,"screen_name","账号"),(au,"avatar_url","头像URL"),
            (T,"likes","喜欢"),(T,"retweets","转帖"),(T,"replies","回复"),(T,"views","查看")]:
    v[n]=act("getvalueforkey",n,WFGetDictionaryValueType="Value",WFDictionaryKey=k,WFInput=att(src))
for src,dst in [("正文","安全正文"),("昵称","安全昵称"),("译文","安全译文")]:
    cur=v[src]
    for f,r in [("&","&amp;"),("<","&lt;"),(">","&gt;")]:
        cur=act("text.replace",dst,WFReplaceTextFind=f,WFReplaceTextReplace=r,WFReplaceTextCaseSensitive=True,WFReplaceTextRegularExpression=False,WFInput=tok([cur]))
    v[dst]=cur
avd=act("downloadurl","头像数据",WFURL=tok([v["头像URL"]]),WFHTTPMethod="GET")
b64=act("base64encode","头像B64",WFEncodeMode="Encode",WFBase64LineBreakMode="None",WFInput=att(avd))
NV=lambda n:{"Type":"Variable","VariableName":n}
RI=NV("Repeat Item")
def rep_start(x):
    gid=str(uuid.uuid4()).upper()
    act("repeat.each",GroupingIdentifier=gid,WFControlFlowMode=0,WFInput=att(x)); return gid
def rep_end(gid):
    A.append({"WFWorkflowActionIdentifier":"is.workflow.actions.repeat.each","WFWorkflowActionParameters":{"GroupingIdentifier":gid,"WFControlFlowMode":2,"UUID":str(uuid.uuid4()).upper()}})
def tile(urlkey,cls,tag):
    u=act("getvalueforkey","媒体URL"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey=urlkey,WFInput=att(RI))
    u2=act("text.replace","去参数URL"+tag,WFReplaceTextFind=r"\?.*$",WFReplaceTextReplace="",WFReplaceTextRegularExpression=True,WFReplaceTextCaseSensitive=False,WFInput=tok([u]))
    full=act("gettext","中图URL"+tag,WFTextActionText=tok([u2,"?name=medium"]))
    dl=act("downloadurl","媒体数据"+tag,WFURL=tok([full]),WFHTTPMethod="GET")
    bb=act("base64encode","媒体B64"+tag,WFEncodeMode="Encode",WFBase64LineBreakMode="None",WFInput=att(dl))
    w=act("getvalueforkey","媒体宽"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey="width",WFInput=att(RI))
    h=act("getvalueforkey","媒体高"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey="height",WFInput=att(RI))
    e=act("calculateexpression","单图高度"+tag,Input=tok(["796*",h,"/",w]))
    r=act("round","单图高度取整"+tag,WFInput=att(e),WFRoundTo="Integer",WFRoundMode="Normal")
    g=cond(2,r); A[-1]["WFWorkflowActionParameters"]["WFNumberValue"]=1200
    act("gettext","封顶"+tag,WFTextActionText="1200")
    other(g); act("gettext","原高"+tag,WFTextActionText=tok([r]))
    hh=endif(g,"If Result")
    act("setvariable",WFVariableName="首图高度",WFInput=att(hh))
    fr=act("gettext","媒体片段"+tag,WFTextActionText=tok(['<div class="'+cls+'" style="--h:',hh,'px"><img src="data:image/jpeg;base64,',bb,'" /></div>']))
    act("appendvariable",WFVariableName="媒体片段",WFInput=att(fr))
md=act("getvalueforkey","媒体",WFGetDictionaryValueType="Value",WFDictionaryKey="media",WFInput=att(T))
gm=cond(100,md)
for key,urlkey,cls,tag in [("photos","url","m","P"),("videos","thumbnail_url","m v","V")]:
    lst=act("getvalueforkey","媒体列表"+tag,WFGetDictionaryValueType="Value",WFDictionaryKey=key,WFInput=att(md))
    gl=cond(100,lst); r0=rep_start(lst); tile(urlkey,cls,tag); rep_end(r0)
    A.append({"WFWorkflowActionIdentifier":"is.workflow.actions.conditional","WFWorkflowActionParameters":{"GroupingIdentifier":gl,"WFControlFlowMode":2,"UUID":str(uuid.uuid4()).upper()}})
A.append({"WFWorkflowActionIdentifier":"is.workflow.actions.conditional","WFWorkflowActionParameters":{"GroupingIdentifier":gm,"WFControlFlowMode":2,"UUID":str(uuid.uuid4()).upper()}})
MEDIA=act("text.combine","媒体HTML",text=att(NV("媒体片段")),WFTextSeparator="Custom",WFTextCustomSeparator=" ")
N=act("count","媒体数",WFCountType="Items",Input=att(NV("媒体片段")))
def ncond(c,val):
    g=cond(c,N); A[-1]["WFWorkflowActionParameters"]["WFNumberValue"]=val; return g
# robust: anything that is not 1/2/>=3 (including empty / missing count) falls through to explicit Number 0
g3=ncond(3,3); act("gettext","三四图块高",WFTextActionText="812"); other(g3)
g2=ncond(4,2); act("gettext","双图块高",WFTextActionText="460"); other(g2)
g1=ncond(4,1); act("calculateexpression","单图块高",Input=tok([NV("首图高度"),"+40"])); other(g1)
act("number","无媒体块高",WFNumberActionNumber=0)
e1=endif(g1,"If Result")
act("gettext","块高b",WFTextActionText=tok([e1]))
e2=endif(g2,"If Result")
act("gettext","块高a",WFTextActionText=tok([e2]))
MH=endif(g3,"If Result")
CJK=r"[\u2E80-\u9FFF\u3000-\u303F\uAC00-\uD7AF\uFF00-\uFFEF]"
def stats(x,tag):
    t=act("count","总字数"+tag,WFCountType="Characters",Input=att(x))
    cm=act("text.match","中文匹配"+tag,WFMatchTextPattern=CJK,WFMatchTextCaseSensitive=False,text=tok([x]))
    c=act("count","中文数"+tag,WFCountType="Items",Input=att(cm))
    nm=act("text.match","换行匹配"+tag,WFMatchTextPattern=r"\n",WFMatchTextCaseSensitive=False,text=tok([x]))
    n=act("count","换行数"+tag,WFCountType="Items",Input=att(nm))
    return t,c,n
t1,c1,n1=stats(v["正文"],"1"); t2,c2,n2=stats(v["译文"],"2")
ex=act("calculateexpression","高度估算",Input=tok(["0.965*(680+(",c1,"/17+(",t1,"-",c1,")/36+",n1,"+1)*68.2+(",c2,"/24+(",t2,"-",c2,")/50+",n2,"+1)*50.7+60)+",MH]))
rh=act("round","高度取整",WFInput=att(ex),WFRoundTo="Integer",WFRoundMode="Normal")
gid=cond(0,rh); A[-1]["WFWorkflowActionParameters"]["WFNumberValue"]=1440
act("gettext","最小高度",WFTextActionText="1440")
other(gid); act("gettext","估算高度",WFTextActionText=tok([rh]))
H0=endif(gid,"If Result")
pg=act("calculateexpression","页数",Input=tok([H0,"/1397.6"]))
pgu=act("round","页数取整",WFInput=att(pg),WFRoundTo="Integer",WFRoundMode="Always Round Up")
sl=act("calculateexpression","分页余量",Input=tok(["(",pgu,"-1)*40"]))
HN=act("calculateexpression","估算高度数值",Input=tok([H0,"+0"]))   # numeric copy so 'greater than' is valid
phl=act("calculateexpression","长页高",Input=tok([HN,"+",sl]))
pbl=act("calculateexpression","长底距",Input=tok(["60+",sl]))
def pick(name,long_ref,short_val):
    g=cond(2,HN); A[-1]["WFWorkflowActionParameters"]["WFNumberValue"]=1440
    act("gettext",name+"长",WFTextActionText=tok([long_ref]) if isinstance(long_ref,dict) else long_ref)
    other(g); act("gettext",name+"短",WFTextActionText=short_val)
    return endif(g,"If Result")
PH=pick("页高",phl,"1440")
PHN=act("calculateexpression","页高数值",Input=tok([PH,"+0"]))
BODY=pick("体高",phl,"1397")
PADB=pick("底距",pbl,"60")
PADT=pick("顶距","60","103")
# ---- v14: style menu (Choose from Menu; Cherri/shortcuts-js layout: start mode 0 with WFMenuItems, one item per mode 1 with WFMenuItemTitle, end mode 2 with UUID)
from styles import STYLES,LABEL,KEYS
mg=str(uuid.uuid4()).upper()
act("choosefrommenu",GroupingIdentifier=mg,WFControlFlowMode=0,WFMenuPrompt="选择风格",WFMenuItems=[LABEL[k] for k in STYLES])
def dictact(name,d):
    items=[{"WFItemType":0,"WFKey":tok([k]),"WFValue":tok([d[k]])} for k in KEYS]
    return act("dictionary",name,WFItems={"Value":{"WFDictionaryFieldValueItems":items},"WFSerializationType":"WFDictionaryFieldValue"})
for k in STYLES:
    act("choosefrommenu",GroupingIdentifier=mg,WFControlFlowMode=1,WFMenuItemTitle=LABEL[k])
    dictact("风格"+LABEL[k],STYLES[k])
mu=str(uuid.uuid4()).upper()
A.append({"WFWorkflowActionIdentifier":"is.workflow.actions.choosefrommenu","WFWorkflowActionParameters":{"GroupingIdentifier":mg,"WFControlFlowMode":2,"UUID":mu}})
STY=ref(mu,"Menu Result")
SV={k:act("getvalueforkey","风格"+k,WFGetDictionaryValueType="Value",WFDictionaryKey=k,WFInput=att(STY)) for k in KEYS}
# ---- end v14 menu
m2={"TEXT":"安全正文","NAME":"安全昵称","HANDLE":"账号","LIKES":"喜欢","RETWEETS":"转帖","REPLIES":"回复","VIEWS":"查看","TRANSLATION":"安全译文"}
extra={"MEDIA":MEDIA}
fixed={"PHOTO":"","PHOTO_DISPLAY":"none","FONT_SIZE":"44","DATE":""}
parts=[]
import os
_template_path=os.path.join(os.path.dirname(os.path.abspath(__file__)),"template.html")
for seg in re.split(r"(\{\{[A-Z_]+\}\})",open(_template_path,encoding="utf-8").read()):
    k=seg[2:-2] if seg.startswith("{{") else None
    if k in fixed: parts.append(fixed[k])
    elif k=="PAGE_HEIGHT": parts.append(PH)
    elif k=="BODY_HEIGHT": parts.append(BODY)
    elif k=="PAD_TOP": parts.append(PADT)
    elif k=="PAD_BOTTOM": parts.append(PADB)
    elif k=="MEDIA": parts.append(MEDIA)
    elif k in SV: parts.append(SV[k])
    elif k=="MEDIA_COUNT": parts.append(N)
    elif k=="AVATAR": parts+=["data:image/jpeg;base64,",b64]
    elif k: parts.append(v[m2[k]])
    else: parts.append(seg)
html=act("gettext","HTML",WFTextActionText=tok(parts))
f=act("setitemname","HTML文件",WFName="card.html",WFDontIncludeFileExtension=False,WFInput=att(html))
pdf=act("makepdf","PDF",WFPDFIncludeMargin=False,WFInput=att(f))
img=act("makeimagefrompdfpage","页面图像",WFMakeImageFromPDFPageColorspace="RGB",WFMakeImageFromPDFPageResolution="96",WFInput=att(pdf))
cb=act("image.combine","拼接图",WFImageCombineMode="Vertically",WFImageCombineSpacing=0,WFInput=att(img))
rs=act("image.resize","卡片图",WFImageResizeWidth="1080",WFImage=att(cb))
cr=act("image.crop","裁剪图",WFImageCropPosition="Top Left",WFImageCropWidth="1080",WFImageCropHeight=tok([PHN]),WFImageCropX="0",WFImageCropY="0",WFInput=att(rs))
act("savetocameraroll",WFInput=att(cr))
wf={"WFWorkflowClientVersion":"2302.0.4","WFWorkflowMinimumClientVersion":900,"WFWorkflowMinimumClientVersionString":"900",
"WFWorkflowIcon":{"WFWorkflowIconStartColor":4282601983,"WFWorkflowIconGlyphNumber":59511},
"WFWorkflowTypes":["ActionExtension"],"WFWorkflowInputContentItemClasses":["WFURLContentItem","WFStringContentItem"],
"WFWorkflowNoInputBehavior":{"Name":"WFWorkflowNoInputBehaviorGetClipboard","Parameters":{}},
"WFWorkflowImportQuestions":[],"WFQuickActionSurfaces":[],"WFWorkflowHasShortcutInputVariables":True,"WFWorkflowActions":A}
_out_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),"shortcut","推特转图.shortcut")
plistlib.dump(wf,open(_out_path,"wb"),fmt=plistlib.FMT_BINARY)
d=plistlib.load(open(_out_path,"rb"))
uu={a["WFWorkflowActionParameters"].get("UUID") for a in d["WFWorkflowActions"]}
def walk(o):
    if isinstance(o,dict):
        if o.get("Type")=="ActionOutput": assert o["OutputUUID"] in uu
        if "attachmentsByRange" in o:
            s=o["string"].encode("utf-16-le")
            for k in o["attachmentsByRange"]: i=int(k[1:].split(",")[0]); assert s[2*i:2*i+2]=="\ufffc".encode("utf-16-le")
        for x in o.values(): walk(x)
    elif isinstance(o,list): [walk(x) for x in o]
walk(d)
# every control-flow group: exactly one start (0) and one end (2), end after start, properly nested
st=[]
for i,a in enumerate(d["WFWorkflowActions"]):
    p=a["WFWorkflowActionParameters"]; m=p.get("WFControlFlowMode"); g=p.get("GroupingIdentifier")
    if m is None: continue
    if m==0: st.append((g,a["WFWorkflowActionIdentifier"]))
    elif m==1: assert st and st[-1][0]==g,("bad middle",i)
    elif m==2: assert st and st[-1]==(g,a["WFWorkflowActionIdentifier"]),("bad end",i); st.pop()
assert not st,st
mn=[a["WFWorkflowActionParameters"] for a in d["WFWorkflowActions"] if a["WFWorkflowActionIdentifier"].endswith("choosefrommenu")]
assert [p["WFMenuItemTitle"] for p in mn if p["WFControlFlowMode"]==1]==mn[0]["WFMenuItems"]
print("control flow nesting OK;",end=" ");print(len(A),"actions, refs+ranges OK")
