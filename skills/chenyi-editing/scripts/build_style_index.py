"""Build an offline gallery, CSV and Markdown from the style registry."""
import csv, html, json
from pathlib import Path
from urllib.parse import quote
ROOT=Path(__file__).resolve().parents[1]/'styles'
def main():
    registry=json.loads((ROOT/'index.json').read_text(encoding='utf-8'))
    rows=registry['styles'];seen=set();cards=[];md=['# 剪辑风格索引','',f"默认：{registry['default_style']}",'','| 编号 | 名称 | 版本 | 状态 | 效果图 |','|---|---|---|---|---|']
    for row in rows:
        if row['id'] in seen:raise ValueError('Duplicate style ID')
        seen.add(row['id'])
        for field in ['profile','preview']:
            p=(ROOT/row[field]).resolve()
            if ROOT.resolve() not in p.parents or not p.is_file():raise ValueError('Missing/invalid '+field)
        title=html.escape(row['id']+'｜'+row['name']);image=quote(row['preview']);profile=quote(row['profile'])
        cards.append(f'<article><img src="{image}" alt="{title} 效果图"><div><p class="badge">{html.escape(row["status"])} · v{html.escape(row["version"])}</p><h2>{title}</h2><p>{html.escape(row.get("description",""))}</p><p class="prompt">这条用 {html.escape(row["id"])} 剪。</p><a href="{image}">打开效果图</a> · <a href="{profile}">查看参数</a></div></article>')
        md.append(f'| {row["id"]} | {row["name"]} | {row["version"]} | {row["status"]} | [查看]({image}) |')
    md+=['','新风格按 CY-002、CY-003 登记；只有已完成参数与效果图的风格才可标 active。旧片保留原样式快照。','']
    for row in rows:md.append(f'![{row["id"]} {row["name"]}]({quote(row["preview"])})\n')
    (ROOT/'风格索引.md').write_text('\n'.join(md),encoding='utf-8')
    with (ROOT/'风格索引.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['id','name','version','status','folder','profile','preview','description']);writer.writeheader();writer.writerows(rows)
    page='''<!doctype html><html lang="zh-CN"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>陈一剪辑 · 风格库</title><style>*{box-sizing:border-box}body{margin:0;background:#f3f2ed;color:#222;font:16px/1.7 system-ui,"Microsoft YaHei",sans-serif}main{max-width:1120px;margin:60px auto;padding:0 24px}header{margin-bottom:36px}small{letter-spacing:.2em;color:#71622c}h1{font-size:42px;line-height:1.2;margin:12px 0}header p{color:#666}article{display:grid;grid-template-columns:minmax(200px,36%) 1fr;gap:32px;background:white;padding:24px;border-radius:18px;margin:22px 0;box-shadow:0 6px 24px #00000008}img{width:100%;border-radius:10px}article>div{padding:20px 0}.badge{font-size:13px;color:#786321}.prompt{background:#f4f1e6;padding:16px;border-radius:8px}a{color:#745b10}footer{color:#777;font-size:14px}@media(max-width:640px){article{grid-template-columns:1fr}h1{font-size:32px}}</style><main><header><small>CHENYI EDITING / STYLE LIBRARY</small><h1>按风格编号，选择下一条视频</h1><p>编号、效果图和剪辑参数放在一起。新片选新风格，旧片保留原版本。</p></header>'''
    page+='<p>当前默认：<b>'+html.escape(registry['default_style'])+'</b></p>'+''.join(cards)+'<footer>效果图为排版示意；本地实际样片另存于用户媒体库。新增风格后运行 build_style_index.py 更新目录。</footer></main></html>'
    (ROOT/'index.html').write_text(page,encoding='utf-8')
    print(f'Indexed {len(rows)} styles')
if __name__=='__main__':main()
