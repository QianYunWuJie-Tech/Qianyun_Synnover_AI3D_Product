"""Publish only verified customer files; retain the previous release for rollback."""
import base64, hashlib, json, os, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/'release-inputs/0.4.4'
OUT = Path(os.environ['RUNNER_TEMP'])/'release044'
OUT.mkdir(exist_ok=True)
REPO = os.environ['GITHUB_REPOSITORY']
TAG = 'v0.4.4'
assert REPO == 'QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product'
def sha(data): return hashlib.sha256(data).hexdigest()
class Redirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        nxt = super().redirect_request(req,fp,code,msg,headers,newurl)
        if nxt is not None and urllib.parse.urlsplit(newurl).netloc != urllib.parse.urlsplit(req.full_url).netloc:
            nxt.remove_header('Authorization')
        return nxt
opener = urllib.request.build_opener(Redirect())
def api(path, method='GET', value=None, raw=False, missing=False):
    url = path if path.startswith('https://') else 'https://api.github.com/repos/'+REPO+'/'+path
    assert urllib.parse.urlsplit(url).netloc in ('api.github.com','uploads.github.com')
    headers = {'Authorization':'Bearer '+os.environ['GH_TOKEN'],
        'Accept':'application/octet-stream' if raw else 'application/vnd.github+json',
        'User-Agent':'synnover-client-release','X-GitHub-Api-Version':'2022-11-28'}
    data = None
    if value is not None:
        data = json.dumps(value).encode(); headers['Content-Type'] = 'application/json'
    try:
        with opener.open(urllib.request.Request(url,headers=headers,data=data,method=method),timeout=300) as r:
            body = r.read()
    except urllib.error.HTTPError as e:
        if missing and e.code == 404: return None
        raise RuntimeError('GitHub API operation failed: '+method+' '+path.split('?')[0]+' HTTP '+str(e.code)) from None
    return body if raw else json.loads(body) if body else None
def add(z,name,data):
    entry=zipfile.ZipInfo(name,(2026,10,14,0,0,0));entry.compress_type=zipfile.ZIP_DEFLATED;entry.external_attr=0o664<<16;z.writestr(entry,data)

manifest = json.loads((INPUT/'manifest.json').read_text())
assert manifest['version']=='0.4.4' and len(manifest['files'])==14 and len(manifest['documents'])==3
assets=[]
for group,folder in [('files','assets'),('documents','docs')]:
    for row in manifest[group]:
        p=INPUT/folder/row['name'];data=p.read_bytes()
        assert sha(data)==row['sha256'] and len(data)==row['size'],p.name
        assets.append(p)
windows=Path(os.environ['RUNNER_TEMP'])/'windows044-output'
receipt=json.loads((windows/'windows044-verification.json').read_text())
assert receipt['passed'] and receipt['product_binaries_unchanged'] and receipt['packaged_cpp_example_compiled']
assert str(receipt['native_build_run'])==str(manifest['qualified_windows']['run'])
assert set(receipt['assets'])=={'SYNNOVER-AI3D-0.4.4-Windows-Setup.exe','SYNNOVER-AI3D-0.4.4-CPP-SDK-Windows.zip'}
for name,row in receipt['assets'].items():
    p=windows/name;data=p.read_bytes();assert sha(data)==row['sha256'] and len(data)==row['size'];assets.append(p)
for platform in ('Linux','Windows'):
    directory=INPUT/'python'/platform;expected=json.loads((directory/'wheels.json').read_text());assert len(expected)==13
    payload={'README.txt':(directory/'README.txt').read_bytes()}
    payload.update({'Examples/'+p.name:p.read_bytes() for p in sorted((directory/'Examples').iterdir())})
    for name,digest in expected.items():
        if name.startswith('synnover_ai3d-0.4.4-'):
            data=(INPUT/'assets'/name).read_bytes()
        else:
            assert name.startswith(('numpy-','pip-')) and name.endswith('.whl')
            with urllib.request.urlopen('https://pypi.org/pypi/'+name.split('-')[0]+'/'+name.split('-')[1]+'/json',timeout=60) as r:
                metadata=json.load(r)
            row=next(a for a in metadata['urls'] if a['filename']==name);assert row['digests']['sha256']==digest
            with urllib.request.urlopen(row['url'],timeout=180) as r:data=r.read()
        assert sha(data)==digest,name
        payload['wheelhouse/'+name]=data
    payload['SHA256SUMS']=''.join(sha(data)+'  '+name+'\n' for name,data in sorted(payload.items())).encode()
    target=OUT/('SYNNOVER-AI3D-0.4.4-Python-SDK-'+platform+'.zip')
    with zipfile.ZipFile(target,'w') as z:
        for name,data in sorted(payload.items()):add(z,name,data)
    assert sha(target.read_bytes())==manifest['python_packages'][target.name],target.name
    with zipfile.ZipFile(target) as z:assert z.testzip() is None
    assets.append(target)
assert len(assets)==21 and len({p.name for p in assets})==21
sums=OUT/'SHA256SUMS';sums.write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(assets)))
assets.append(sums)
release=api('releases/tags/'+TAG,missing=True)
if release is None:
    release=api('releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],
        'name':'SYNNOVER AI3D 0.4.4','draft':True,'prerelease':False,'body':(INPUT/'RELEASE_NOTES.md').read_text()})
current={a['name']:a for a in api('releases/'+str(release['id'])+'/assets?per_page=100')}
assert set(current)<={p.name for p in assets},'Unexpected existing release asset'
verified=[]
for p in assets:
    data=p.read_bytes();digest=sha(data);a=current.get(p.name)
    if a:
        if sha(api('releases/assets/'+str(a['id']),raw=True))!=digest:
            assert release['draft'],'Refuse to replace an already published artifact'
            api('releases/assets/'+str(a['id']),'DELETE');a=None
    if a is None:
        assert release['draft'],'Published asset missing'
        url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(p.name)
        req=urllib.request.Request(url,data=data,method='POST',headers={
            'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','User-Agent':'synnover-client-release'})
        with opener.open(req,timeout=300) as r:a=json.load(r)
    assert sha(api('releases/assets/'+str(a['id']),raw=True))==digest,'Read-back mismatch: '+p.name
    verified.append({'name':p.name,'sha256':digest,'size':len(data)})
    print('Uploaded and read back',p.name,flush=True)
final=api('releases/'+str(release['id'])+'/assets?per_page=100')
assert {a['name'] for a in final}=={p.name for p in assets}
release=api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'true'})
assert api('releases/latest')['tag_name']==TAG
# Switch the customer download page only after every new link is public.
page=api('contents/README.md');new_page=(INPUT/'README044.md').read_bytes()
if base64.b64decode(page['content'])!=new_page:
    api('contents/README.md','PUT',{'message':'Update customer downloads to 0.4.4','sha':page['sha'],
        'content':base64.b64encode(new_page).decode(),'branch':'main'})
report={'passed':True,'version':'0.4.4','tag':TAG,'url':release['html_url'],'assets':verified,
    'previous_0_4_3_retained':api('releases/tags/v0.4.3')['draft'] is False,
    'windows_qualification':receipt,'source_commit':os.environ['GITHUB_SHA']}
(OUT/'publication-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Published',release['html_url'],flush=True)
