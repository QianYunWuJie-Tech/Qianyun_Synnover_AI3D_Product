import ctypes, hashlib, os, subprocess, sys, tempfile, time

from pathlib import Path

KEY = r'Software\Microsoft\Windows\CurrentVersion\Uninstall\SYNNOVER-AI3D'

def run(args, **kwargs):
    timeout = kwargs.pop('timeout', 180)
    with tempfile.TemporaryFile(mode='w+', encoding='utf-8') as log:
        process = subprocess.Popen(list(map(str, args)), stdout=log, stderr=subprocess.STDOUT, **kwargs)
        try:
            process.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            if sys.platform == 'win32':
                subprocess.run(['taskkill', '/PID', str(process.pid), '/T', '/F'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=20)
            else:
                process.kill()
            process.wait(timeout=20)
            log.seek(0)
            output = log.read()
            print(output, flush=True)
            raise subprocess.TimeoutExpired(list(map(str, args)), timeout, output=output)
        log.seek(0)
        output = log.read()
        print(output, flush=True)
    result = subprocess.CompletedProcess(list(map(str, args)), process.returncode, stdout=output)
    result.check_returncode()
    return result

def sha(path):
    with Path(path).open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def installer_checks(previous, installer, work):
    import winreg
    if not ctypes.windll.shell32.IsUserAnAdmin():
        raise RuntimeError('Isolated installer CI requires an administrator host')
    try:
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY):
            raise RuntimeError('Refuse to modify an existing customer installation')
    except FileNotFoundError:
        pass
    checks = []

    def nsis(exe, tail='', good=True):
        command = '"' + str(Path(exe).resolve()) + '" /S' + (' ' + tail if tail else '')
        result = subprocess.run(command, executable=str(Path(exe).resolve()), timeout=180)
        if good and result.returncode:
            raise RuntimeError('Native NSIS failed: ' + str(result.returncode))
        return result.returncode

    def present(directory):
        assert (directory / 'bin/cleardepth-viewer.exe').is_file()
        with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, KEY, 0, winreg.KEY_READ | winreg.KEY_WOW64_64KEY) as key:
            assert winreg.QueryValueEx(key, 'InstallerRevision')[0] == 2
            assert Path(winreg.QueryValueEx(key, 'InstallLocation')[0]) == directory

    def firewall(directory, remove=False):
        run(['powershell.exe', '-NoProfile', '-ExecutionPolicy', 'Bypass', '-File', directory / 'firewall.ps1', *(['-Remove'] if remove else [])])

    def firewall_path():
        script = "(Get-NetFirewallRule -Name 'SYNNOVER-AI3D-Discovery' -ErrorAction Stop | Get-NetFirewallApplicationFilter).Program"
        return subprocess.check_output(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script], text=True).strip()
    old = work / '相机 旧版本'
    new = work / '相机 新版本'
    nsis(previous, '/D=' + str(old))
    (old / 'customer-record.txt').write_text('keep', encoding='utf-8')
    firewall(old)
    nsis(installer)
    present(old)
    assert (old / 'customer-record.txt').read_text() == 'keep'
    assert Path(firewall_path()) == old / 'bin/cleardepth-viewer.exe'
    checks.append('previous shipped installer upgrades in registered Unicode path and restores enabled firewall rule')
    nsis(installer)
    present(old)
    checks.append('same-version reinstall')
    nsis(installer, '/D=' + str(new))
    present(new)
    assert not (old / 'bin/cleardepth-viewer.exe').exists() and (old / 'customer-record.txt').is_file()
    assert Path(firewall_path()) == new / 'bin/cleardepth-viewer.exe'
    checks.append('directory migration preserves customer files and moves firewall rule')
    create = ctypes.windll.kernel32.CreateFileW
    create.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    create.restype = ctypes.c_void_p
    close = ctypes.windll.kernel32.CloseHandle
    close.argtypes = [ctypes.c_void_p]
    handle = create(str(new / 'bin/cleardepth-viewer.exe'), 2147483648, 1, None, 3, 0, None)
    if handle == ctypes.c_void_p(-1).value:
        raise ctypes.WinError()
    try:
        uninstaller = sha(new / 'Uninstall.exe')
        assert nsis(installer, good=False) != 0
        present(new)
        assert sha(new / 'Uninstall.exe') == uninstaller
        assert nsis(new / 'Uninstall.exe', '_?=' + str(new), good=False) != 0
        present(new)
        checks.append('locked executable refuses upgrade and uninstall before deleting registration')
    finally:
        close(handle)
    (new / 'customer-final.txt').write_text('keep', encoding='utf-8')
    nsis(new / 'Uninstall.exe')
    for _ in range(200):
        if not (new / 'bin/cleardepth-viewer.exe').exists() and (not (new / 'Uninstall.exe').exists()):
            break
        time.sleep(0.1)
    assert not (new / 'bin/cleardepth-viewer.exe').exists()
    assert (new / 'customer-final.txt').is_file()
    script = "if (Get-NetFirewallRule -Name 'SYNNOVER-AI3D-Discovery' -ErrorAction SilentlyContinue) {exit 1}"
    run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command', script])
    checks.append('ordinary uninstall removes program and firewall rule while preserving customer files')
    return checks
