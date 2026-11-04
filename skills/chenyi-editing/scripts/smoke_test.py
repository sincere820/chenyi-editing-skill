"""Synthetic behavioral test. Creates its own fixture; never touches user footage."""
import argparse,json,subprocess,sys
from pathlib import Path
from natural_pause_cut import read_json,write_json,digest,approved_cuts,build_map
from remap_plan import remap

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--work',required=True);ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--ffprobe',default='ffprobe');ap.add_argument('--font',required=True);a=ap.parse_args()
    root=Path(a.work).resolve()
    if root.exists():raise FileExistsError('Use a fresh test directory')
    root.mkdir(parents=True);scripts=Path(__file__).resolve().parent
    def run(cmd,ok=True):
        r=subprocess.run([str(x) for x in cmd],capture_output=True,text=True,encoding='utf-8',errors='replace')
        if (r.returncode==0)!=ok:raise AssertionError(r.stdout+'\n'+r.stderr)
        return r
    checks=[];src=root/'fixture.mp4'
    expr='if(lt(t,2),0.2*sin(2*PI*440*t),if(lt(t,2.6),0,if(lt(t,4.6),0.2*sin(2*PI*440*t),if(lt(t,6),0,0.2*sin(2*PI*440*t)))))'
    run([a.ffmpeg,'-v','error','-n','-f','lavfi','-i','color=c=0x314c61:s=320x568:r=30:d=8','-f','lavfi','-i',f'aevalsrc={expr}:s=48000:d=8'.replace(expr,"'"+expr+"'"),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-c:a','aac',src])
    original=digest(src);planfile=root/'pauses.json'
    base=[sys.executable,scripts/'natural_pause_cut.py',src,'--ffmpeg',a.ffmpeg,'--ffprobe',a.ffprobe,'--plan',planfile]
    run(base);p=read_json(planfile)
    short=next(c for c in p['candidates'] if 1.8<c['silence_start']<2.2)
    long=next(c for c in p['candidates'] if 4.4<c['silence_start']<4.8)
    assert short['proposed_action']=='shorten' and long['proposed_action']=='review'
    assert not approved_cuts(p);checks.append('detect_short_and_long_pauses_without_auto_approval')
    rough=root/'rough.mp4'
    run(base+['--render','--output',rough],False);assert not rough.exists();checks.append('reject_unreviewed_render')
    short.update(decision='shorten',reviewed=True,review_reason='Synthetic fixture: known zero signal, no speech/emotion, test-only approval')
    write_json(planfile,p);run(base+['--render','--output',rough]);m=read_json(rough.with_suffix('.time-map.json'))
    assert .3<m['removed']<.5 and m['technical']=='pass';checks.append('synchronized_trim_decode_duration')
    run(base+['--render','--output',src],False);assert digest(src)==original;checks.append('source_unchanged_and_overwrite_rejected')
    project=root/'project'
    run([sys.executable,scripts/'init_project.py','--source',src,'--project',project,'--font',a.font,'--ffmpeg',a.ffmpeg,'--ffprobe',a.ffprobe,'--title-top','陈一剪辑样式测试','--title-bottom','保留自然语义气口'])
    e=read_json(project/'edit-plan.json')
    e['captions']=[dict(start=.2,end=1.8,text='这是样式测试'),dict(start=2.7,end=4.4,text='这是另一句测试')]
    e['assets']={'clip':dict(path=str(src))};e['broll']=[dict(start=1.7,end=3.2,source_in=.5,asset_id='clip',label='测试素材',reason='Synthetic remap test')]
    q=remap(e,m)
    assert len(q['broll'])==2 and abs(q['captions'][1]['start']-(2.7-m['removed']))<1e-5
    assert abs(q['broll'][1]['source_in']-(.5+m['keep'][1]['source_in']-1.7))<1e-5
    checks.append('captions_and_broll_retime_with_source_offset')
    bad=dict(e,captions=[dict(start=1.9,end=2.8,text='不可猜测跨切词')])
    try:remap(bad,m)
    except ValueError:checks.append('reject_caption_crossing_removed_speech_boundary')
    else:raise AssertionError('Cross-cut caption accepted')
    still=root/'still.png';run([a.ffmpeg,'-v','error','-n','-i',src,'-frames:v','1',still])
    q['assets']['still']=dict(path=str(still),type='image')
    q['broll'].append(dict(start=5,end=6,source_in=0,asset_id='still',label='静图测试',reason='Still support'))
    q['broll'].sort(key=lambda b:b['start'])
    # Exercise project-relative media and fonts; tool paths stay machine-specific and explicit.
    q['source']='../rough.mp4';q['assets']['clip']['path']='../fixture.mp4';q['assets']['still']['path']='../still.png'
    finalplan=project/'remapped.json';write_json(finalplan,q)
    final=root/'final.mp4'
    run([sys.executable,scripts/'render_edit.py',finalplan,'--output',final])
    assert read_json(final.with_suffix('.review.json'))['technical']=='pass';checks.append('relative_paths_still_and_video_subtitles_full_render')
    run([sys.executable,scripts/'render_edit.py',finalplan,'--output',final],False);checks.append('existing_render_not_overwritten')
    result=dict(status='pass',checks=checks,scope='Synthetic audio/video only, not human semantic or listening validation',python=sys.version,source_sha256=original,font_sha256=digest(a.font))
    write_json(root/'test-results.json',result);print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
