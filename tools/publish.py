"""Publish the fixed 0.4.3 customer downloads after checking every artifact."""
import hashlib,json,os,urllib.request,urllib.parse,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'release-inputs/0.4.3';OUT=Path(os.environ['RUNNER_TEMP'])/'release043';OUT.mkdir(exist_ok=True)
REPO=os.environ['GITHUB_REPOSITORY'];TAG='v0.4.3';assert REPO=='QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product'
def sha(b):return hashlib.sha256(b).hexdigest()
def api(path,method='GET',value=None,raw=False):
 url=path if path.startswith('https://') else 'https://api.github.com/repos/'+REPO+'/'+path
 headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/octet-stream' if raw else 'application/vnd.github+json','User-Agent':'synnover-downloads','X-GitHub-Api-Version':'2022-11-28'}
 data=None
 if value is not None:data=json.dumps(value).encode();headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers,data=data,method=method),timeout=300) as r:b=r.read()
 return b if raw else json.loads(b) if b else None
def add(z,name,b):
 i=zipfile.ZipInfo(name,(2026,10,14,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o644<<16;z.writestr(i,b)
manifest=json.loads((INPUT/'manifest.json').read_text());assert manifest['version']=='0.4.3' and len(manifest['files'])==16
assets=[]
for group,subdir in [('files','assets'),('documents','docs')]:
 for row in manifest[group]:
  p=INPUT/subdir/row['name'];b=p.read_bytes();assert sha(b)==row['sha256'] and len(b)==row['size'];assets.append(p)
for platform in ('Linux','Windows'):
 t=INPUT/'python'/platform;expected=json.loads((t/'wheels.json').read_text());assert len(expected)==13;wheels={}
 for name,digest in expected.items():
  if name.startswith('synnover_ai3d-0.4.3-'):b=(INPUT/'assets'/name).read_bytes()
  else:
   assert name.startswith(('numpy-','pip-')) and name.endswith('.whl')
   with urllib.request.urlopen('https://pypi.org/pypi/'+name.split('-')[0]+'/'+name.split('-')[1]+'/json',timeout=60) as r:metadata=json.load(r)
   a=next(a for a in metadata['urls'] if a['filename']==name);assert a['digests']['sha256']==digest
   with urllib.request.urlopen(a['url'],timeout=180) as r:b=r.read()
  assert sha(b)==digest,name;wheels[name]=b
 p=OUT/('SYNNOVER-AI3D-0.4.3-Python-SDK-'+platform+'.zip')
 with zipfile.ZipFile(p,'x') as z:
  add(z,'README.txt',(t/'README.txt').read_bytes())
  for f in sorted((t/'Examples').iterdir()):add(z,'Examples/'+f.name,f.read_bytes())
  for f in sorted((INPUT/'docs').iterdir()):add(z,'Docs/'+f.name,f.read_bytes())
  for name,b in sorted(wheels.items()):add(z,'wheelhouse/'+name,b)
  add(z,'SHA256SUMS',('\n'.join(sha(b)+'  wheelhouse/'+n for n,b in sorted(wheels.items()))+'\n').encode())
 with zipfile.ZipFile(p) as z:assert z.testzip() is None
 assets.append(p)
assert len(assets)==21 and len({p.name for p in assets})==21
sums=OUT/'SHA256SUMS';sums.write_text('\n'.join(sha(p.read_bytes())+'  '+p.name for p in assets)+'\n');assets.append(sums)
notes=(INPUT/'RELEASE_NOTES.md').read_text();releases=api('releases?per_page=100');release=next((r for r in releases if r['tag_name']==TAG),None)
if release is None:release=api('releases','POST',{'tag_name':TAG,'name':'SYNNOVER AI3D 0.4.3','body':notes,'draft':True,'prerelease':False,'make_latest':'false'})
verified=[]
for p in assets:
 current=api('releases/'+str(release['id'])+'/assets?per_page=100');a=next((a for a in current if a['name']==p.name),None);b=p.read_bytes()
 if a is None:
  url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(p.name)
  req=urllib.request.Request(url,data=b,method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','User-Agent':'synnover-downloads'})
  with urllib.request.urlopen(req,timeout=300) as r:a=json.load(r)
 assert a['name']==p.name
 assert sha(api('releases/assets/'+str(a['id']),raw=True))==sha(b),'Release read-back mismatch: '+p.name
 verified.append({'name':p.name,'sha256':sha(b),'size':len(b),'url':a['browser_download_url']});print('Verified',p.name,sha(b),flush=True)
release=api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'true','body':notes})
assert not release['draft'] and not release['prerelease']
# Only the superseded public download release is retired. Private history is separate.
old=next((r for r in releases if r['tag_name']=='client-2026.10.14'),None)
if old:
 api('releases/'+str(old['id']),'DELETE')
 try:api('git/refs/tags/client-2026.10.14','DELETE')
 except urllib.error.HTTPError as e:
  if e.code!=404:raise
assert api('releases/latest')['tag_name']==TAG
(OUT/'verification.json').write_text(json.dumps({'passed':True,'tag':TAG,'assets':verified,'retired_public_tag':'client-2026.10.14'},indent=2))
print('Published',release['html_url'],flush=True)
