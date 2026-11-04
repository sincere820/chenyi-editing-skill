"""Select a registered style without changing source media or existing projects."""
import argparse, copy, json
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]/'styles'
def load_style(style_id=None):
    registry=json.loads((ROOT/'index.json').read_text(encoding='utf-8'))
    wanted=style_id or registry['default_style']
    matches=[row for row in registry['styles'] if row['id']==wanted]
    if len(matches)!=1:raise ValueError('Unknown or duplicate style ID: '+wanted)
    row=matches[0]
    if row['status']!='active':raise ValueError('Style is not active: '+wanted)
    path=(ROOT/row['profile']).resolve()
    if ROOT.resolve() not in path.parents:raise ValueError('Profile must stay in styles folder')
    return row,json.loads(path.read_text(encoding='utf-8'))

def apply_style(plan, row, profile):
    old=plan['style'];new=copy.deepcopy(profile['style'])
    for key in ['font_file','fonts_dir','font_family']:
        if key in old:new[key]=old[key]
    if len(old['title_lines'])!=len(new['title_lines']):
        raise ValueError('Map title text to new layout explicitly')
    for a,b in zip(new['title_lines'],old['title_lines']):a['text']=b['text']
    for field in ['identity','footer','vertical']:
        previous=old.get(field,[]);target=new.get(field,[])
        if previous and target:
            if len(previous)!=len(target):raise ValueError('Map '+field+' text to new layout explicitly')
            for a,b in zip(target,previous):
                for key in ['text','glyphs']:
                    if key in b:a[key]=copy.deepcopy(b[key])
        else:new[field]=copy.deepcopy(previous)
    result=copy.deepcopy(plan);result.update(style=new,style_id=row['id'],style_version=row['version'])
    return result

def main():
    ap=argparse.ArgumentParser(description=__doc__);sub=ap.add_subparsers(dest='command',required=True)
    sub.add_parser('list');p=sub.add_parser('apply');p.add_argument('plan');p.add_argument('--style-id',required=True);p.add_argument('--output',required=True)
    a=ap.parse_args()
    if a.command=='list':
        print((ROOT/'index.json').read_text(encoding='utf-8'));return
    source=Path(a.plan).resolve();dest=Path(a.output).resolve()
    if dest.exists():raise FileExistsError('Choose a new output plan')
    # Relative media paths remain valid only when the output stays beside the input.
    if source.parent!=dest.parent:raise ValueError('Keep new plan beside original to preserve relative media paths')
    row,profile=load_style(a.style_id)
    result=apply_style(json.loads(source.read_text(encoding='utf-8-sig')),row,profile)
    dest.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(dest)

if __name__=='__main__':main()
