"""Read a pinned public SDK and create a fresh draw-only app build."""
import importlib
import json
from pathlib import Path
import subprocess
import sys
from .source import check_source
from .spec import validate

SDK_COMMIT='547e7ac7e1af8eedf1dc063f97a27a93425f50b7'


def load_sdk(path):
    path=Path(path).absolute()
    try:
        if path.resolve()!=path:raise ValueError()
        actual=subprocess.check_output(['git','-C',str(path),'rev-parse','HEAD'],text=True,stderr=subprocess.DEVNULL).strip()
        modified=subprocess.check_output(['git','-C',str(path),'status','--porcelain','--untracked-files=no'],text=True)
        if actual!=SDK_COMMIT or modified.strip():raise ValueError()
    except (OSError,ValueError,subprocess.CalledProcessError):raise ValueError('clean pinned public OS SDK required') from None
    sys.path.insert(0,str(path/'prototypes/lab-os'))
    sdk=importlib.import_module('labos.project')
    if sdk.ROOT!=path:raise ValueError('another SDK is already loaded')
    return sdk


def build_game(spec,source,output,sdk_root):
    spec=validate(spec);check_source(source);sdk=load_sdk(sdk_root)
    output=Path(output).absolute()
    if output.is_symlink():raise ValueError('real output directory required')
    output=output.parent.resolve()/output.name
    if output.exists():raise ValueError('fresh game output required')
    output.mkdir(parents=True)
    config={key:spec[key] for key in ('id','title','version')};config['capabilities']=['draw']
    (output/'app.json').write_text(json.dumps(config,sort_keys=True)+'\n')
    (output/'app.c').write_text(source)
    result=sdk.build_project(output)
    return dict(result,capabilities=['draw'],sdk_commit=SDK_COMMIT)
