"""Publish a reviewed customer milestone; verify all assets before making it public."""
import hashlib,json,os,subprocess,time,urllib.request,urllib.parse,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];INPUT=ROOT/'release-inputs/2026-10-14';OUT=Path(os.environ['RUNNER_TEMP'])/'customer-release';OUT.mkdir(exist_ok=True)
REPO=os.environ['GITHUB_REPOSITORY'];TAG='client-2026.10.14'
assert REPO=='QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product'
def sha(data):return hashlib.sha256(data).hexdigest()
def api(path,method='GET',value=None,raw=False):
 url=path if path.startswith('https://') else 'https://api.github.com/repos/'+REPO+'/'+path
 headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Accept':'application/octet-stream' if raw else 'application/vnd.github+json','User-Agent':'synnover-public-release','X-GitHub-Api-Version':'2022-11-28'}
 data=None
 if value is not None:data=json.dumps(value).encode();headers['Content-Type']='application/json'
 with urllib.request.urlopen(urllib.request.Request(url,headers=headers,data=data,method=method),timeout=300) as r:b=r.read()
 return b if raw else json.loads(b) if b else None
def add(z,n,d):
 i=zipfile.ZipInfo(n,(2026,10,13,0,0,0));i.compress_type=zipfile.ZIP_DEFLATED;i.external_attr=0o644<<16;z.writestr(i,d)
manifest=json.loads((INPUT/'manifest.json').read_text());assets=[]
for entry in manifest['files']:
 p=INPUT/'assets'/entry['name'];data=p.read_bytes();assert sha(data)==entry['sha256'] and len(data)==entry['size'],p.name
 assets.append(p)
for platform in ('Linux','Windows'):
 root=INPUT/'package-inputs'/platform;expected=json.loads((root/'expected.json').read_text());wheels={}
 for name,digest in sorted(expected['wheel_hashes'].items()):
  if name.startswith('synnover_ai3d-'):data=(INPUT/'assets'/name).read_bytes()
  else:
   assert name.startswith('numpy-') and name.endswith('.whl')
   with urllib.request.urlopen('https://pypi.org/pypi/numpy/'+name.split('-')[1]+'/json',timeout=60) as r:meta=json.load(r)
   entry=next(e for e in meta['urls'] if e['filename']==name);assert entry['digests']['sha256']==digest
   with urllib.request.urlopen(entry['url'],timeout=180) as r:data=r.read()
  assert sha(data)==digest,name;wheels[name]=data
 p=OUT/('SYNNOVER-AI3D-0.4.2-rc.3-Python-SDK-'+platform+'.zip')
 with zipfile.ZipFile(p,'w') as z:
  for n in ['README.txt','Docs/Python-API.html','Examples/camera.py','Examples/capture.py','Examples/orientation.py','Examples/nanning_camera.py']:add(z,n,(root/n).read_bytes())
  for n,d in sorted(wheels.items()):add(z,'wheelhouse/'+n,d)
  add(z,'verification.json',(root/'verification.json').read_bytes())
  add(z,'SHA256SUMS',('\n'.join(sha(d)+'  wheelhouse/'+n for n,d in sorted(wheels.items()))+'\n').encode())
 assert sha(p.read_bytes())==expected['sha256'],'Original Python SDK release hash mismatch: '+platform
 assets.append(p);print('Original SDK archive matched:',platform,flush=True)
for p in sorted((INPUT/'docs').iterdir()):
 assert p.suffix=='.html';assets.append(p)
rows=[{'name':p.name,'size':p.stat().st_size,'sha256':sha(p.read_bytes())} for p in assets];assert len(rows)==len({r['name'] for r in rows})
checks=OUT/'SHA256SUMS';checks.write_text('\n'.join(r['sha256']+'  '+r['name'] for r in rows)+'\n');assets.append(checks)
notes=(INPUT/'RELEASE_NOTES.md').read_text();release=None
for page in range(1,10):
 rs=api('releases?per_page=100&page='+str(page));release=next((r for r in rs if r['tag_name']==TAG),None)
 if release or len(rs)<100:break
if not release:release=api('releases','POST',{'tag_name':TAG,'name':'SYNNOVER AI3D 客户端下载 · 2026-10-14','body':notes,'draft':True,'prerelease':True,'make_latest':'false'})
verified=[]
def upload(p):
 existing=api('releases/'+str(release['id'])+'/assets?per_page=100');asset=next((a for a in existing if a['name']==p.name),None);data=p.read_bytes()
 if not asset:
  url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(p.name)
  req=urllib.request.Request(url,data=data,method='POST',headers={'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','User-Agent':'synnover-public-release'})
  with urllib.request.urlopen(req,timeout=300) as r:asset=json.load(r)
 assert asset['name']==p.name
 downloaded=api('releases/assets/'+str(asset['id']),raw=True);assert sha(downloaded)==sha(data),'Release readback differs: '+p.name
 verified.append({'name':p.name,'sha256':sha(data),'size':len(data),'url':asset['browser_download_url']});print('Uploaded and downloaded SHA verified:',p.name,flush=True)
for p in assets:upload(p)
report={'passed':True,'tag':TAG,'repository':REPO,'commit':os.environ['GITHUB_SHA'],'components':manifest['components'],'scope':manifest['scope'],'assets':verified}
p=OUT/'release-verification.json';p.write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n');upload(p)
release=api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':True,'make_latest':'false','body':notes});assert not release['draft'];print('Published:',release['html_url'])
