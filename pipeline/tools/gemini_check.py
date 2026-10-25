import sys,json,wave,re,difflib,numpy as np,sherpa_onnx,unicodedata
ep,lang=sys.argv[1],sys.argv[2]; ids=sys.argv[3:]
SLOW={'es':0.13,'pt':0.13,'de':0.12,'en':0.12,'ja':0.30,'zh':0.33}[lang]
M='/home/claude/models/sherpa-onnx-whisper-base/'
r=sherpa_onnx.OfflineRecognizer.from_whisper(encoder=M+'base-encoder.int8.onnx',decoder=M+'base-decoder.int8.onnx',tokens=M+'base-tokens.txt',language=lang,task='transcribe',num_threads=2)
def norm(s):
    s=unicodedata.normalize('NFKD',s.lower()); s=''.join(c for c in s if not unicodedata.combining(c))
    return re.sub(r"[^\w]","",s)
plan=json.load(open(ep+'/tts/plan.json'))
epj=json.load(open(ep+'/episode.json'))
def sub(c):
    out=[]
    for sc,li in c['lines']:
        l=epj['scenes'][sc]['lines'][li]; out.append(l if isinstance(l,str) else l[0])
    return ' '.join(out)
rates=[]
for c in plan['chunks']:
    if ids and c['id'] not in ids: continue
    try: w=wave.open(f"{ep}/tts/{c['id']}.wav")
    except FileNotFoundError: print(c['id'],'MISSING');continue
    sr=w.getframerate();a=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(np.float32)/32768
    s=r.create_stream();s.accept_waveform(sr,a);r.decode_stream(s);t=s.result.text.strip()
    A,B=norm(sub(c)),norm(t)
    sp=len(a)/sr/max(1,len(norm(c['text']))); ratio=len(B)/max(1,len(A)); sim=difflib.SequenceMatcher(None,A,B).ratio()
    flag=('<<<' if ratio>1.25 or ratio<0.75 or sim<0.7 else '')+(' SLOW' if sp>SLOW else '')
    print(f"{c['id']:9s} {len(a)/sr:5.1f}s {sp:.3f} len{ratio:4.2f} sim{sim:4.2f} {flag} | {t}")
