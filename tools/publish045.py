"""Publish only verified customer files; retain the previous release for rollback."""
import base64, hashlib, json, os, urllib.error, urllib.parse, urllib.request, zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/'release-inputs/0.4.5'
OUT = Path(os.environ['RUNNER_TEMP'])/'release045'
OUT.mkdir(exist_ok=True)
REPO = os.environ['GITHUB_REPOSITORY']
TAG = 'v0.4.5'
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
manifest=json.loads((INPUT/'manifest.json').read_text())
assert manifest['version']=='0.4.5' and manifest['windows_local_build_passed'] and manifest['windows_wine_tests_passed'] and manifest['diagnostics_transport_passed']
expected={'SYNNOVER-AI3D-0.4.5-Windows-Setup.exe','SYNNOVER-AI3D-0.4.5-Windows-Portable.zip','SYNNOVER-AI3D-0.4.5-x86_64.AppImage','SYNNOVER-AI3D-0.4.5-Manual.html'}
assert set(manifest['files'])==expected
assets=[]
for name,row in manifest['files'].items():
    p=INPUT/'assets'/name;data=p.read_bytes()
    assert sha(data)==row['sha256'] and len(data)==row['size']
    assets.append(p)
sums=OUT/'SHA256SUMS';sums.write_text(''.join(sha(p.read_bytes())+'  '+p.name+'\n' for p in sorted(assets)))
assets.append(sums)
release=api('releases/tags/'+TAG,missing=True)
if release is None:
    release=api('releases','POST',{'tag_name':TAG,'target_commitish':os.environ['GITHUB_SHA'],
        'name':'SYNNOVER AI3D Viewer 0.4.5','draft':True,'prerelease':False,'body':(INPUT/'RELEASE_NOTES.md').read_text()})
current={a['name']:a for a in api('releases/'+str(release['id'])+'/assets?per_page=100')}
assert set(current)<={p.name for p in assets},'Unexpected release asset'
verified=[]
for p in assets:
    data=p.read_bytes();digest=sha(data);a=current.get(p.name)
    if a:
        assert sha(api('releases/assets/'+str(a['id']),raw=True))==digest,'Existing artifact differs; preserve it and investigate'
    else:
        assert release['draft'],'Refuse to add to published release'
        url=release['upload_url'].split('{')[0]+'?name='+urllib.parse.quote(p.name)
        req=urllib.request.Request(url,data=data,method='POST',headers={
            'Authorization':'Bearer '+os.environ['GH_TOKEN'],'Content-Type':'application/octet-stream','User-Agent':'synnover-viewer-release'})
        with opener.open(req,timeout=300) as r:a=json.load(r)
    assert sha(api('releases/assets/'+str(a['id']),raw=True))==digest
    verified.append({'name':p.name,'sha256':digest,'size':len(data)})
    print('Uploaded and read back',p.name,flush=True)
assert {a['name'] for a in api('releases/'+str(release['id'])+'/assets?per_page=100')}=={p.name for p in assets}
release=api('releases/'+str(release['id']),'PATCH',{'draft':False,'prerelease':False,'make_latest':'true'})
assert api('releases/latest')['tag_name']==TAG
page=api('contents/README.md');new_page=(INPUT/'README045.md').read_bytes()
if base64.b64decode(page['content'])!=new_page:
    api('contents/README.md','PUT',{'message':'Publish Viewer 0.4.5 downloads; retain SDK 0.4.4','sha':page['sha'],
        'content':base64.b64encode(new_page).decode(),'branch':'main'})
report={'passed':True,'version':'0.4.5','tag':TAG,'url':release['html_url'],'assets':verified,
    'previous_0_4_4_retained':api('releases/tags/v0.4.4')['draft'] is False,'source_commit':os.environ['GITHUB_SHA']}
(OUT/'publication-verification.json').write_text(json.dumps(report,indent=2)+'\n')
print('Published',release['html_url'],flush=True)
