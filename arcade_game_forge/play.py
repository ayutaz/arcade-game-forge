"""Play the unchanged accepted package in the existing Mac OS host window."""
import hashlib
import importlib
import json
from pathlib import Path
import re
import tempfile
from .sdk import load_sdk
from .spec import validate


def ready_package(run):
    run=Path(run).resolve();result=json.loads((run/'result.json').read_text())
    ready=result.get('ready',{})
    if result.get('accepted') is not True or result.get('status')!='finished' or ready.get('passed') is not True:
        raise ValueError('accepted finished run required')
    if type(ready.get('folder')) is not str or not re.fullmatch(r'attempt-[1-5]/game',ready['folder']):
        raise ValueError('owned ready folder required')
    file=run/ready['folder']/'build/app.labapp'
    if file.is_symlink() or not file.resolve().is_relative_to(run) or file.stat().st_size>16384:
        raise ValueError('bounded package inside run required')
    package=file.read_bytes()
    if hashlib.sha256(package).hexdigest()!=ready.get('package_sha256'):raise ValueError('ready package changed')
    spec=validate(json.loads((run/'spec.json').read_text()))
    if hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()!=result.get('spec_sha256'):
        raise ValueError('run spec changed')
    return spec,package


def play(run,sdk_root,*,max_frames=None,window=None):
    if max_frames is not None and (type(max_frames) is not int or not 1<=max_frames<=60000):
        raise ValueError('finite frame bounds')
    spec,package=ready_package(run);load_sdk(sdk_root)
    decode=importlib.import_module('labos.package').decode
    Home=importlib.import_module('labos.home').Home
    Repository=importlib.import_module('labos.repository').Repository
    if window is None:window=importlib.import_module('labos.cli').run_window
    manifest,blob=decode(package)
    if any(manifest[key]!=spec[key] for key in ('id','title','version')) or manifest['capabilities']!=['draw']:
        raise ValueError('trusted game metadata required')
    with tempfile.TemporaryDirectory() as tmp:
        home=Home(Repository(Path(tmp).resolve()/'apps'))
        try:
            home.install(manifest,blob);home.frame(16,0);home.frame(0,0)
            if home.mode!='running':raise ValueError('fixed app did not start')
            frames=window(home,max_frames=max_frames)
        finally:home.close()
        if home.ledger.count:raise ValueError('host resources not released')
    return dict(frames=frames,host_only=True,device_tested=False,package_sha256=hashlib.sha256(package).hexdigest())
