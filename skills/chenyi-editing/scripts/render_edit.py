"""Render a reversible talking-head/B-roll plan with FFmpeg and ASS.

Only reads source media. Output and intermediates live under --output's folder.
v1 supports an unchanged master speech timeline, not ripple cuts or speed changes.
"""
import argparse, hashlib, json, subprocess, os, shutil
from pathlib import Path
from PIL import ImageFont

def run(cmd):
    result=subprocess.run([str(v) for v in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if result.returncode:
        raise RuntimeError(result.stderr[-6000:])
    return result.stdout

def probe(exe,path):
    return json.loads(run([exe,'-v','error','-show_format','-show_streams','-of','json',path]))

def ass_time(t):
    c=round(t*100);h,c=divmod(c,360000);m,c=divmod(c,6000);s,c=divmod(c,100)
    return f'{h}:{m:02}:{s:02}.{c:02}'

def srt_time(t):
    ms=round(t*1000);h,ms=divmod(ms,3600000);m,ms=divmod(ms,60000);s,ms=divmod(ms,1000)
    return f'{h:02}:{m:02}:{s:02},{ms:03}'

def safe_text(t):
    return str(t).replace('\\','').replace('{','').replace('}','').replace('\n','\\N')

def subtitles(plan,spans,duration,path):
    st=plan['style']; font=st['font_family']
    header='[Script Info]\nScriptType: v4.00+\nPlayResX: 1080\nPlayResY: 1920\nWrapStyle: 2\nScaledBorderAndShadow: yes\n[V4+ Styles]\n'
    header+='Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n'
    header+=f'Style: Base,{font},82,&H00FFFFFF,&H00FFFFFF,&H00222222,&H22000000,0,0,0,0,100,100,0,0,1,0.6,0,5,40,40,0,1\n'
    header+='[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\n'
    events=[]
    def add(a,b,text,x,y,size,color='FFFFFF',align=5,layer=2):
        a=max(0,a);b=min(duration,b)
        if b<=a:return
        rgb=color; bgr=rgb[4:6]+rgb[2:4]+rgb[0:2]
        # ASS em-height differs from the visible glyph size for Source Han Serif.
        # This factor is a measured profile setting, not a global font rule.
        rendered_size=round(size*st.get('ass_size_multiplier',1),2)
        shadow=f'{{\\an{align}\\pos({x+5},{y+5})\\fs{rendered_size}\\c&H000000&\\alpha&H{st.get('shadow_alpha','00')}&\\bord0\\shad0\\blur4}}'
        events.append(f'Dialogue: 0,{ass_time(a)},{ass_time(b)},Base,,0,0,0,,{shadow}{safe_text(text)}')
        tags=f'{{\\an{align}\\pos({x},{y})\\fs{rendered_size}\\c&H{bgr}&}}'
        events.append(f'Dialogue: {layer},{ass_time(a)},{ass_time(b)},Base,,0,0,0,,{tags}{safe_text(text)}')
    for line in st['title_lines']:
        add(0,duration,line['text'],540,line['y'],line['size'],line['color'])
    srt=[]
    for c in plan['captions']:
        if c['start']>=duration:continue
        measured=ImageFont.truetype(st['font_file'],st['caption_size']).getlength(c['text'])
        size=st['caption_size']*min(1,st.get('max_caption_width',970)/max(measured,1))
        add(c['start'],c['end'],c['text'],540,st['caption_y'],size)
        srt.append(f"{len(srt)+1}\n{srt_time(c['start'])} --> {srt_time(min(c['end'],duration))}\n{c['text']}\n")
    for sp in spans:
        if sp['kind']=='host':
            for line in st.get('identity',[]):
                add(sp['start'],sp['end'],line['text'],line['x'],line['y'],line['size'],line['color'],align=4)
        elif sp.get('label'):
            add(sp['start'],sp['end'],sp['label'],540,1780,30,layer=1)
    for line in st.get('footer',[]):
        add(0,duration,line['text'],line['x'],line['y'],line['size'],line['color'])
    for column in st.get('vertical',[]):
        for i,glyph in enumerate(column['glyphs']):
            add(0,duration,glyph,column['x'],column['y']+i*column['step'],column['size'],column['color'])
    path.write_text(header+'\n'.join(events)+'\n',encoding='utf-8-sig')
    path.with_suffix('.srt').write_text('\n'.join(srt),encoding='utf-8')

def main():
    ap=argparse.ArgumentParser();ap.add_argument('plan');ap.add_argument('--output',required=True);ap.add_argument('--end',type=float);ap.add_argument('--check-only',action='store_true');args=ap.parse_args()
    planfile=Path(args.plan).resolve();p=json.loads(planfile.read_text(encoding='utf-8-sig'))
    base=planfile.parent
    def resolve(value):return str((base/Path(value)).resolve())
    p['source']=resolve(p['source'])
    for asset in p['assets'].values():asset['path']=resolve(asset['path'])
    for key in ['font_file','fonts_dir']:p['style'][key]=resolve(p['style'][key])
    for key in ['ffmpeg','ffprobe']:
        value=p['tools'][key]
        p['tools'][key]=shutil.which(value) or resolve(value)
    ff=p['tools']['ffmpeg'];fp=p['tools']['ffprobe'];master=Path(p['source']);fps=p['fps']
    if fps!=30:raise ValueError('This profile is validated at 30fps; convert deliberately, do not claim added motion detail')
    if Path(args.output).resolve()==master or (Path(args.output).exists() and not args.check_only):raise ValueError('Choose a new output; never overwrite source or existing renders')
    metadata=probe(fp,master);source_duration=float(metadata['format']['duration'])
    end=min(args.end if args.end is not None else p['duration'],p['duration'])
    total=round(end*fps);end=total/fps
    if end>source_duration+1/fps:raise ValueError('Output exceeds source duration')
    if p.get('cuts') or p.get('speed',1)!=1:raise ValueError('v1 does not support cuts/speed; needs explicit timeline remapping')
    broll=sorted(p['broll'],key=lambda x:x['start']);last=0
    for b in broll:
        if b['start']<last or b['end']<=b['start'] or b['end']>p['duration'] or not 0<=b.get('focus_x',.5)<=1:raise ValueError('Overlapping/out-of-range B-roll or crop focus')
        last=b['end'];asset=p['assets'][b['asset_id']]
        if not Path(asset['path']).is_file():raise ValueError('Missing asset '+asset['path'])
        if asset.get('type')!='image':
            ad=float(probe(fp,asset['path'])['format']['duration'])
            if b['source_in']<0 or b['source_in']+(b['end']-b['start'])>ad:raise ValueError('Asset too short')
    last=0
    for c in p['captions']:
        if c['start']<last-0.0001 or c['end']<=c['start'] or c['end']>p['duration']:raise ValueError('Caption timing invalid')
        if len(c['text'])>13:raise ValueError('Caption exceeds 13 characters: '+c['text'])
        last=c['end']
    spans=[];cursor=0
    for b in broll:
        a=round(b['start']*fps);z=min(total,round(b['end']*fps))
        if a>=total:break
        if a>cursor:spans.append({'kind':'host','start':cursor/fps,'end':a/fps,'source_in':cursor/fps,'path':str(master)})
        sp={'kind':'broll','start':a/fps,'end':z/fps,'source_in':b['source_in'],'path':p['assets'][b['asset_id']]['path'],'label':b.get('label'),'focus_x':b.get('focus_x',0.5)}
        sp['media_type']=p['assets'][b['asset_id']].get('type','video')
        spans.append(sp);cursor=z
    if cursor<total:spans.append({'kind':'host','start':cursor/fps,'end':end,'source_in':cursor/fps,'path':str(master)})
    out=Path(args.output).resolve();folder=out.parent;folder.mkdir(parents=True,exist_ok=True)
    editing=folder/'editing';editing.mkdir(exist_ok=True)
    ass=editing/(out.stem+'.ass');subtitles(p,spans,end,ass)
    print(json.dumps({'duration':end,'spans':len(spans),'captions':sum(c['start']<end for c in p['captions'])}),flush=True)
    if args.check_only:return
    parts=folder/'picture-cache';parts.mkdir(exist_ok=True)
    outputs=[]
    for i,sp in enumerate(spans):
        frames=round((sp['end']-sp['start'])*fps)
        if frames<=0:raise ValueError('Zero-length span')
        vfilter=f"scale=1080:1920:force_original_aspect_ratio=increase,crop=1080:1920:(in_w-1080)*{sp.get('focus_x',0.5)}:(in_h-1920)/2,fps={fps},setsar=1"
        # Cache only if source stat, rendering settings, and span exactly match.
        key=hashlib.sha256(json.dumps([sp,Path(sp['path']).stat().st_mtime_ns,frames,vfilter],sort_keys=True).encode()).hexdigest()[:12]
        part=parts/f'{i:03}-{key}.mp4';outputs.append(part)
        if not part.exists():
            input_args=['-loop','1','-framerate',fps,'-i',sp['path']] if sp.get('media_type')=='image' else ['-ss',sp['source_in'],'-i',sp['path']]
            run([ff,'-hide_banner','-loglevel','error','-y',*input_args,'-an','-vf',vfilter,'-frames:v',frames,'-c:v','libx264','-preset','veryfast','-crf','19','-threads','2','-pix_fmt','yuv420p',part])
        print(f'Picture {i+1}/{len(spans)} ready',flush=True)
    listing=parts/'concat.txt';listing.write_text('\n'.join("file '"+v.as_posix().replace("'","'\\''")+"'" for v in outputs),encoding='utf-8')
    visual=parts/'visual.mp4';run([ff,'-hide_banner','-loglevel','error','-y','-f','concat','-safe','0','-i',listing,'-c','copy',visual])
    ass_path=ass.as_posix().replace(':','\\:');fonts=Path(p['style']['fonts_dir']).as_posix().replace(':','\\:')
    run([ff,'-hide_banner','-loglevel','error','-y','-i',visual,'-i',master,'-map','0:v:0','-map','1:a:0','-vf',f"ass='{ass_path}':fontsdir='{fonts}'",'-t',end,'-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out])
    actual=probe(fp,out)
    if abs(float(actual['format']['duration'])-end)>0.08:raise RuntimeError('Rendered duration mismatch')
    run([ff,'-hide_banner','-v','error','-i',out,'-f','null',os.devnull])
    sha=hashlib.sha256(out.read_bytes()).hexdigest()
    review={'video':str(out),'sha256':sha,'plan_sha256':hashlib.sha256(planfile.read_bytes()).hexdigest(),'duration':end,'technical':'pass','frame_review':'not_done','continuous_playback':'not_done','listening':'not_done','user_feedback':'not_done','note':'Original speech retained. No BGM added. Font fallback explicitly recorded in plan.','spans':spans}
    (folder/(out.stem+'.review.json')).write_text(json.dumps(review,ensure_ascii=False,indent=2),encoding='utf-8')
    print(out,flush=True)

if __name__=='__main__':main()
