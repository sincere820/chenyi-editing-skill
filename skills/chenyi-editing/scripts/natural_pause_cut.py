"""Conservative acoustic candidates, explicitly reviewed cuts, synchronized rough cut.
Python 3.10+, FFmpeg/ffprobe. No third-party Python dependency.
"""
import argparse, hashlib, json, math, re, subprocess
from pathlib import Path

def run(argv):
    p=subprocess.run([str(x) for x in argv],capture_output=True,text=True,encoding='utf-8',errors='replace')
    if p.returncode: raise RuntimeError(p.stderr[-5000:])
    return p

def digest(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
    return h.hexdigest()

def read_json(p):return json.loads(Path(p).read_text(encoding='utf-8-sig'))
def write_json(p,v):Path(p).write_text(json.dumps(v,ensure_ascii=False,indent=2),encoding='utf-8')
def probe(fp,src):return json.loads(run([fp,'-v','error','-show_streams','-show_format','-of','json',src]).stdout)

def build_map(duration,cuts):
    cursor=0.;dest=0.;rows=[]
    for a,b in cuts+[(duration,duration)]:
        if a<cursor or b<a or b>duration:raise ValueError('Cuts overlap or exceed source')
        if a>cursor:
            rows.append(dict(source_in=cursor,source_out=a,timeline_in=dest,timeline_out=dest+a-cursor,speed=1))
            dest+=a-cursor
        cursor=b
    if not rows:raise ValueError('Cannot remove the entire source')
    return rows

def approved_cuts(plan):
    cuts=[]
    for c in plan['candidates']:
        decision=c.get('decision','review')
        if decision not in ['keep','review','shorten','delete']:raise ValueError('Unknown decision')
        if decision in ['keep','review']:continue
        if c.get('reviewed') is not True or not c.get('review_reason'):
            raise ValueError('Each cut requires reviewed=true and a listening/semantic review_reason')
        a,b=map(float,c['cut'])
        if not all(map(math.isfinite,[a,b])):raise ValueError('Non-finite cut')
        if not (c['silence_start']<=a<b<=c['silence_end']):raise ValueError('Cut outside detected pause')
        cuts.append((a,b))
    return sorted(cuts)

def analyze(src,args):
    m=probe(args.ffprobe,src)
    if not any(s['codec_type']=='audio' for s in m['streams']):raise ValueError('Source has no audio')
    if not any(s['codec_type']=='video' for s in m['streams']):raise ValueError('This renderer requires video')
    duration=float(m['format']['duration'])
    log=run([args.ffmpeg,'-hide_banner','-i',src,'-map','0:a:0','-af',f'silencedetect=noise={args.db}dB:d={args.trigger}','-f','null','-']).stderr
    spans=[];start=None
    for match in re.finditer(r'silence_(start|end):\s*([\d.]+)',log):
        kind,t=match.group(1),min(duration,float(match.group(2)))
        if kind=='start':start=max(0,t)
        elif start is not None:spans.append((start,t));start=None
    if start is not None:spans.append((start,duration))
    candidates=[]
    for i,(a,b) in enumerate(spans):
        long=b-a>=args.skip_long;edge=a<=.05 or b>=duration-.05
        protection=max(args.retain/2,args.guard)
        cut=[round(a+protection,6),round(b-protection,6)]
        useful=cut[1]-cut[0]>=args.min_cut
        suggested='review' if long or edge else ('shorten' if useful else 'keep')
        candidates.append(dict(id=f'pause-{i+1:03}',silence_start=a,silence_end=b,
            measured_duration=b-a,proposed_action=suggested,decision='review' if useful else 'keep',
            cut=cut if useful else None,reviewed=False,review_reason='',breath_types=[],
            note='Long or edge pause: retain pending review' if long or edge else 'Low level only; listening and semantics required'))
    return dict(schema_version=1,source=str(src),source_sha256=digest(src),source_duration=duration,
        parameters=dict(db=args.db,trigger=args.trigger,retain=args.retain,skip_long=args.skip_long,guard=args.guard,min_cut=args.min_cut),
        candidates=candidates,status='analysis_only',potential_reduction=sum(c['cut'][1]-c['cut'][0] for c in candidates if c['proposed_action']=='shorten'),
        planned_reduction=0,warning='Silence is not permission to cut. No pause has been approved automatically.')

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('input');ap.add_argument('--plan');ap.add_argument('--output');ap.add_argument('--render',action='store_true')
    ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--ffprobe',default='ffprobe')
    ap.add_argument('--db',type=float,default=-35);ap.add_argument('--trigger',type=float,default=.38)
    ap.add_argument('--retain',type=float,default=.20);ap.add_argument('--skip-long',type=float,default=1.20)
    ap.add_argument('--guard',type=float,default=.06);ap.add_argument('--min-cut',type=float,default=.15)
    a=ap.parse_args();src=Path(a.input).resolve()
    if not all(math.isfinite(x) for x in [a.db,a.trigger,a.retain,a.skip_long,a.guard,a.min_cut]):raise ValueError('Finite parameters required')
    if min(a.trigger,a.retain,a.skip_long,a.guard,a.min_cut)<=0:raise ValueError('Positive timing parameters required')
    planpath=Path(a.plan).resolve() if a.plan else src.with_name(src.stem+'_pause_plan.json')
    if not a.render:
        if planpath.exists():raise FileExistsError('Refusing to overwrite an existing reviewed plan')
        planpath.parent.mkdir(parents=True,exist_ok=True);p=analyze(src,a);write_json(planpath,p)
        print(json.dumps(dict(plan=str(planpath),candidates=len(p['candidates']),status=p['status']),ensure_ascii=False));return
    if not a.plan or not a.output:raise ValueError('--render requires an existing --plan and a new --output')
    p=read_json(planpath)
    if p.get('source_sha256')!=digest(src):raise ValueError('Source differs from reviewed plan')
    cuts=approved_cuts(p)
    if not cuts:raise ValueError('No explicitly reviewed cuts; keep using original source')
    mapping=build_map(p['source_duration'],cuts)
    out=Path(a.output).resolve()
    if out==src or out.exists():raise FileExistsError('Never overwrite source or an existing output')
    out.parent.mkdir(parents=True,exist_ok=True)
    filters=[];labels=[]
    for i,k in enumerate(mapping):
        filters.extend([f"[0:v:0]trim=start={k['source_in']}:end={k['source_out']},setpts=PTS-STARTPTS[v{i}]",
                        f"[0:a:0]atrim=start={k['source_in']}:end={k['source_out']},asetpts=PTS-STARTPTS[a{i}]"])
        labels.append(f'[v{i}][a{i}]')
    filters.append(''.join(labels)+f'concat=n={len(mapping)}:v=1:a=1[v][a]')
    graph=out.with_suffix('.filters.txt');graph.write_text(';\n'.join(filters),encoding='utf-8')
    run([a.ffmpeg,'-hide_banner','-v','error','-n','-i',src,'-filter_complex_script',graph,'-map','[v]','-map','[a]',
         '-c:v','libx264','-preset','veryfast','-crf','18','-threads','2','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',out])
    actual=probe(a.ffprobe,out);expected=mapping[-1]['timeline_out']
    if abs(float(actual['format']['duration'])-expected)>.12:raise RuntimeError('Duration mismatch; inspect output before using')
    run([a.ffmpeg,'-v','error','-i',out,'-f','null','-'])
    result=dict(schema_version=1,source=str(src),source_sha256=p['source_sha256'],output=str(out),output_sha256=digest(out),
        source_duration=p['source_duration'],duration=expected,removed=p['source_duration']-expected,cuts=cuts,keep=mapping,
        technical='pass',listening='not_done',motion_review='not_done',status='rough_cut_pending_listening')
    write_json(out.with_suffix('.time-map.json'),result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':main()
