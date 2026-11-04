"""Remap an original-source edit plan after reviewed pause cuts. Never guess cut speech."""
import argparse,copy,json
from pathlib import Path
from natural_pause_cut import read_json,write_json,digest

def intersections(a,b,mapping):
    return [(max(a,k['source_in']),min(b,k['source_out']),k) for k in mapping if min(b,k['source_out'])>max(a,k['source_in'])]
def at(t,k):return k['timeline_in']+t-k['source_in']
def remap(p,m):
    q=copy.deepcopy(p);q['source']=m['output'];q['duration']=m['duration'];q.pop('cuts',None);q['speed']=1
    q['captions']=[];q['broll']=[]
    for c in p['captions']:
        pieces=intersections(c['start'],c['end'],m['keep'])
        covered=sum(b-a for a,b,k in pieces)
        if abs(covered-(c['end']-c['start']))>1e-5 or len(pieces)!=1:
            raise ValueError('Caption crosses removed interval; realign its spoken words first: '+c['text'])
        a,b,k=pieces[0];q['captions'].append(dict(c,start=round(at(a,k),6),end=round(at(b,k),6)))
    for c in p['broll']:
        for a,b,k in intersections(c['start'],c['end'],m['keep']):
            si=c['source_in']+(a-c['start']) if p['assets'][c['asset_id']].get('type')!='image' else 0
            q['broll'].append(dict(c,start=round(at(a,k),6),end=round(at(b,k),6),source_in=si))
    q['source_time_map']=m;q['timing_basis']='Remapped from reviewed source keep intervals'
    return q

def main():
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('plan');ap.add_argument('time_map');ap.add_argument('--output',required=True);a=ap.parse_args()
    p=read_json(a.plan);m=read_json(a.time_map);base=Path(a.plan).resolve().parent
    def resolve(s):return str((base/Path(s)).resolve())
    p['source']=resolve(p['source'])
    for asset in p['assets'].values():asset['path']=resolve(asset['path'])
    for key in ['font_file','fonts_dir']:
        if p['style'].get(key):p['style'][key]=resolve(p['style'][key])
    if digest(p['source'])!=m['source_sha256']:raise ValueError('Edit plan source does not match time map')
    if digest(m['output'])!=m['output_sha256']:raise ValueError('Rough cut changed since mapping')
    if Path(a.output).exists():raise FileExistsError('Choose a new plan path')
    write_json(a.output,remap(p,m));print(a.output)
if __name__=='__main__':main()
