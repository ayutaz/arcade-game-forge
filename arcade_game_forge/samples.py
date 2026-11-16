"""Rebuild the recorded AI-generated samples; this path never calls a model."""
import hashlib
import json
from pathlib import Path
from .pipeline import forge
from .source import check_source
from .spec import validate

ROOT=Path(__file__).resolve().parents[1]


def load_sample(kind):
    if kind not in ('maze','collect','dodge'):raise ValueError('sample kind')
    folder=ROOT/'examples/games'/kind
    metadata=json.loads((folder/'provenance.json').read_text())
    source=(folder/'app.c').read_text()
    if hashlib.sha256(source.encode()).hexdigest()!=metadata['source_sha256']:raise ValueError('bundled AI source changed')
    spec=validate(json.loads((folder/'spec.json').read_text()))
    if hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest()!=metadata['spec_sha256']:
        raise ValueError('bundled specification changed')
    return spec,check_source(source)


def build_sample(kind,output,sdk_root):
    spec,source=load_sample(kind)
    result=forge(spec,output,sdk_root,generator=lambda prompt,workspace:source,max_attempts=1)
    result['origin']='bundled_sample_rebuild'
    (Path(output)/'result.json').write_text(json.dumps(result,indent=2)+'\n')
    return result
