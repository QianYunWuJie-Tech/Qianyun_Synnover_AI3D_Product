"""Refresh manuals around qualified native Windows binaries, then test installation."""
import hashlib, json, os, shutil, subprocess, tempfile, urllib.request, zipfile
from pathlib import Path
from verify_installer import installer_checks

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT / 'release-inputs/0.4.4'
OUT = Path(os.environ['RUNNER_TEMP']) / 'windows044-output'
OUT.mkdir()
manifest = json.loads((INPUT / 'manifest.json').read_text())
assert manifest['version'] == '0.4.4'
assert os.name == 'nt' and os.environ.get('GITHUB_ACTIONS') == 'true'
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def add(z, name, data):
    info = zipfile.ZipInfo(name, (2026,10,14,0,0,0))
    info.compress_type = zipfile.ZIP_DEFLATED
    info.external_attr = 0o664 << 16
    z.writestr(info, data)

with tempfile.TemporaryDirectory(prefix='synnover044-', dir=os.environ['RUNNER_TEMP']) as folder:
    work = Path(folder)
    original = INPUT / 'windows' / 'SYNNOVER-AI3D-0.4.4-Windows-Portable.zip'
    assert sha(original) == manifest['qualified_windows']['portable_sha256']
    with zipfile.ZipFile(original) as archive:
        assert archive.testzip() is None
        for name in archive.namelist():
            assert name.startswith('SYNNOVER-AI3D/') and '\\' not in name and '..' not in Path(name).parts
        archive.extractall(work)
    payload = work / 'SYNNOVER-AI3D'
    original_binaries = {p.relative_to(payload).as_posix(): sha(p) for p in payload.rglob('*') if p.suffix.lower() in ('.dll','.exe','.lib')}
    shutil.rmtree(payload / 'Docs')
    (payload / 'Docs').mkdir()
    for row in manifest['documents']:
        p = INPUT / 'docs' / row['name']
        assert sha(p) == row['sha256'] and p.stat().st_size == row['size']
        name = 'SYNNOVER-AI3D-0.4.4-Manual.html' if 'Customer-Manual' in p.name else p.name
        shutil.copyfile(p, payload / 'Docs' / name)
    assert all(sha(payload / name) == digest for name, digest in original_binaries.items())
    def nsis_path(p):
        return p.relative_to(payload).as_posix().replace('/', '\\').replace('$','$$').replace('"','$\\"')
    rows = ['; Remove shipped files only; preserve customer data.']
    rows += ['Delete "$INSTDIR\\' + nsis_path(p) + '"' for p in sorted(payload.rglob('*')) if p.is_file()]
    rows += ['RMDir "$INSTDIR\\' + nsis_path(p) + '"' for p in sorted(payload.rglob('*'),key=lambda p:len(p.parts),reverse=True) if p.is_dir()]
    uninstall = work / 'uninstall.nsh'
    uninstall.write_text('\n'.join(rows)+'\n',encoding='utf-8-sig')
    nsis = Path(r'C:\Program Files (x86)\NSIS')
    installer = OUT / 'SYNNOVER-AI3D-0.4.4-Windows-Setup.exe'
    subprocess.run([str(nsis/'makensis.exe'),'/V2','/DPRODUCT_VERSION=0.4.4',
        '/DPRODUCT_PAYLOAD='+str(payload),'/DPRODUCT_PAYLOAD_GLOB='+str(payload/'*'),
        '/DPRODUCT_INSTALLER='+str(installer),'/DPRODUCT_UNINSTALL_LIST='+str(uninstall),'candidate.nsi'],
        cwd=INPUT/'windows/installer',env=dict(os.environ,NSISDIR=str(nsis)),check=True)
    previous = work / 'previous-0.4.3.exe'
    with urllib.request.urlopen('https://github.com/QianYunWuJie-Tech/Qianyun_Synnover_AI3D_Product/releases/download/v0.4.3/SYNNOVER-AI3D-0.4.3-Windows-Setup.exe',timeout=180) as r:
        previous.write_bytes(r.read())
    assert sha(previous) == 'c06dc2e33f46d262c368e62b752b9e7fa64cef4f5b0ddc63496e1ebcee4e0f83'
    checks = installer_checks(previous, installer, work)
    cpp = work / 'cpp'
    for directory in ('bin','include','lib'):
        shutil.copytree(payload/directory,cpp/'sdk'/directory)
    (cpp/'sdk/bin/cleardepth-viewer.exe').unlink()
    shutil.copytree(payload/'share/cleardepth-viewer/licenses',cpp/'licenses')
    shutil.copytree(INPUT/'windows/Examples',cpp/'Examples')
    (cpp/'README.txt').write_text('SYNNOVER AI3D 0.4.4 C++ SDK\n\n使用说明与接口参考：\nhttps://my.feishu.cn/docx/ESuAdQpqFo4jwIxijEjcb217nId\n',encoding='utf-8')
    (cpp/'SHA256SUMS').write_text(''.join(sha(p)+'  '+p.relative_to(cpp).as_posix()+'\n' for p in sorted(cpp.rglob('*')) if p.is_file()))
    sdk = OUT / 'SYNNOVER-AI3D-0.4.4-CPP-SDK-Windows.zip'
    with zipfile.ZipFile(sdk,'x') as z:
        for p in sorted(cpp.rglob('*')):
            if p.is_file(): add(z,p.relative_to(cpp).as_posix(),p.read_bytes())
    # Compile the example from the actual customer package, including DLL deployment.
    subprocess.run(['cmake','-S',str(cpp/'Examples'),'-B',str(work/'consumer'),'-A','x64'],check=True)
    subprocess.run(['cmake','--build',str(work/'consumer'),'--config','Release'],check=True)
    assert (work/'consumer/Release/first-frame.exe').is_file()
    assert (work/'consumer/Release/synnover_ai3d.dll').is_file()
    with zipfile.ZipFile(sdk) as z:
        assert z.testzip() is None and not any('Docs' in Path(n).parts for n in z.namelist())
    receipt = {'passed':True,'version':'0.4.4','native_build_run':manifest['qualified_windows']['run'],
        'native_source_commit':manifest['qualified_windows']['source_commit'],
        'qualified_native_binary_sha256':original_binaries,'product_binaries_unchanged':True,
        'installer_checks':checks,'packaged_cpp_example_compiled':True,
        'windows_live_camera_qualified':False,
        'assets':{p.name:{'sha256':sha(p),'size':p.stat().st_size} for p in (installer,sdk)}}
    (OUT/'windows044-verification.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Windows customer packaging and installation checks passed',flush=True)
