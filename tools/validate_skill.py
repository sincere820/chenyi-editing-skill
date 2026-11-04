"""Validate this source layout and preserve every v2.0.0 archive file/script."""
import ast, hashlib, json, re, zipfile
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit
import yaml

ROOT=Path(__file__).resolve().parents[1]
SKILL=ROOT/'skills/chenyi-editing'
def main():
    text=(SKILL/'SKILL.md').read_text(encoding='utf-8')
    match=re.match(r'^---\n(.*?)\n---\n',text,re.S)
    assert match,'Missing YAML frontmatter'
    meta=yaml.safe_load(match.group(1))
    assert re.fullmatch(r'[a-z0-9]+(?:-[a-z0-9]+)*',meta['name'])
    assert meta['name']==SKILL.name and len(meta['name'])<=64
    assert isinstance(meta['description'],str) and 0<len(meta['description'])<=1024
    assert set(meta)<= {'name','description','compatibility','license','metadata','allowed-tools'}
    assert 'license' not in meta,'Do not add an unconfirmed license'
    if 'metadata' in meta:assert all(isinstance(k,str) and isinstance(v,str) for k,v in meta['metadata'].items())
    links=[]
    def check_link(path,link):
        target=urlsplit(link)
        if target.scheme or not target.path:return
        resolved=(path.parent/unquote(target.path)).resolve()
        assert ROOT.resolve()==resolved or ROOT.resolve() in resolved.parents,(path,link)
        assert resolved.exists(),f'Broken relative link: {path.relative_to(ROOT)} -> {link}'
        links.append((str(path.relative_to(ROOT)),link))
    for path in [ROOT/'README.md',ROOT/'RIGHTS.md',*SKILL.rglob('*.md')]:
        content=path.read_text(encoding='utf-8')
        for link in re.findall(r'!?\[[^\]]*\]\(([^)]+)\)',content):check_link(path,link)
    class Links(HTMLParser):
        def handle_starttag(self,tag,attrs):
            for k,v in attrs:
                if k in ('href','src') and v:check_link(self.path,v)
    for path in SKILL.rglob('*.html'):
        parser=Links();parser.path=path;parser.feed(path.read_text(encoding='utf-8'))
    scripts=list((SKILL/'scripts').glob('*.py'))
    for path in scripts:ast.parse(path.read_text(encoding='utf-8'),filename=str(path))
    for path in SKILL.rglob('*.json'):json.loads(path.read_text(encoding='utf-8-sig'))
    registry=json.loads((SKILL/'styles/index.json').read_text(encoding='utf-8'))
    assert len({x['id'] for x in registry['styles']})==len(registry['styles'])
    assert registry['default_style'] in {x['id'] for x in registry['styles']}
    for row in registry['styles']:
        for field in ['folder','profile','preview']:check_link(SKILL/'styles/index.json',row[field])
    unchanged=[];changed=[]
    with zipfile.ZipFile(ROOT/'chenyi-editing-v2.0.0.zip') as archive:
        for name in archive.namelist():
            if not name.startswith('skills/chenyi-editing/') or name.endswith('/'):continue
            path=ROOT/name;assert path.is_file(),f'Original file missing: {name}'
            equal=path.read_bytes()==archive.read(name)
            (unchanged if equal else changed).append(name)
            if '/scripts/' in name:assert equal,f'Original script changed: {name}'
    result={'status':'pass','archive_files_preserved':len(unchanged)+len(changed),'byte_identical_files':len(unchanged),'changed_original_files':changed,'original_scripts_unchanged':len(scripts),'relative_links_checked':len(links),'zip_sha256':hashlib.sha256((ROOT/'chenyi-editing-v2.0.0.zip').read_bytes()).hexdigest(),'scope':'Structural checks only; media paths in example JSON are intentional placeholders; external links and real speech not tested'}
    print(json.dumps(result,ensure_ascii=False,indent=2))
if __name__=='__main__':main()
