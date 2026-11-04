"""Preflight tools/font and create a portable project plan (no edits or downloads)."""
import argparse,json,shutil,subprocess
from pathlib import Path
from PIL import ImageFont

def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--source',required=True);ap.add_argument('--project',required=True)
    ap.add_argument('--font',required=True);ap.add_argument('--font-family',default='Source Han Serif SC Heavy')
    ap.add_argument('--ffmpeg',default='ffmpeg');ap.add_argument('--ffprobe',default='ffprobe')
    ap.add_argument('--title-top',required=True);ap.add_argument('--title-bottom',required=True)
    ap.add_argument('--style-id',default=None,help='Registry style ID, e.g. CY-001')
    ap.add_argument('--identity-profile',help='Local identity/AI-label JSON; do not share private paths')
    a=ap.parse_args();dest=Path(a.project).resolve();source=Path(a.source).resolve();font=Path(a.font).resolve()
    if dest.exists() and any(dest.iterdir()):raise ValueError('Choose an empty project folder')
    if not source.is_file() or not font.is_file():raise FileNotFoundError('Source/font missing')
    ImageFont.truetype(str(font),82)
    tools={}
    for key,value in [('ffmpeg',a.ffmpeg),('ffprobe',a.ffprobe)]:
        binary=shutil.which(value) or str(Path(value).resolve())
        subprocess.run([binary,'-version'],check=True,capture_output=True);tools[key]=binary
    filters=subprocess.run([tools['ffmpeg'],'-filters'],capture_output=True,text=True).stdout
    if ' ass ' not in filters and ' ass ' not in filters.replace('\r',''):raise ValueError('FFmpeg needs libass / ass filter')
    meta=json.loads(subprocess.check_output([tools['ffprobe'],'-v','error','-show_streams','-show_format','-of','json',str(source)]))
    if not any(s['codec_type']=='audio' for s in meta['streams']):raise ValueError('Source has no speech audio')
    video=next(s for s in meta['streams'] if s['codec_type']=='video')
    n,d=map(float,video['avg_frame_rate'].split('/'))
    if abs(n/d-30)>.01:raise ValueError('Reference renderer requires 30fps source; prepare an explicit 30fps derivative first')
    from style_registry import load_style
    selected,profile=load_style(a.style_id)
    style=profile['style'];style.update(font_file=str(font),fonts_dir=str(font.parent),font_family=a.font_family)
    if a.identity_profile:
        identity=json.loads(Path(a.identity_profile).read_text(encoding='utf-8-sig'))
        for field in ['identity','vertical','footer']:
            if field in identity:style[field]=identity[field]
    style['title_lines'][0]['text']=a.title_top;style['title_lines'][1]['text']=a.title_bottom
    for line in style['title_lines']:
        if ImageFont.truetype(str(font),int(line['size'])).getlength(line['text'])>970:
            raise ValueError('Title too wide: shorten it or tune style deliberately')
    dest.mkdir(parents=True,exist_ok=True)
    for name in ['analysis','downloads','subtitles','preview']: (dest/name).mkdir(exist_ok=True)
    plan=dict(schema_version=1,style_id=selected['id'],style_version=selected['version'],source=str(source),duration=float(meta['format']['duration']),fps=30,speed=1,tools=tools,style=style,captions=[],assets={},broll=[])
    (dest/'edit-plan.json').write_text(json.dumps(plan,ensure_ascii=False,indent=2),encoding='utf-8')
    (dest/'analysis/source-metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(dict(project=str(dest),status='initialized_not_edited',next='Transcribe/correct captions; review pauses; select B-roll; fill plan. Identity is blank until supplied.'),ensure_ascii=False))
if __name__=='__main__':main()
