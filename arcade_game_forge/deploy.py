"""Dedicated Forge IDs only; no firmware, removal or unrelated-app updates."""
import hashlib
import re

IDS={'forge-maze','forge-dodge','forge-collect'}


def install_game(client,package,decode,*,previous_sha=None):
    manifest,_=decode(package);name=manifest['id']
    if name not in IDS or manifest['capabilities']!=['draw'] or len(package)>16384:
        raise ValueError('dedicated draw-only Forge package required')
    if previous_sha is not None and (type(previous_sha) is not str or not re.fullmatch('[0-9a-f]{64}',previous_sha)):
        raise ValueError('previous package hash')
    status=client.control_status()
    if status['mode']!=0 or status['held'] or status['remaining_ms'] or status['active_id']:
        raise ValueError('HOME with released keys required')
    before=client.list_apps()
    if len({row['id'] for row in before})!=len(before):raise ValueError('catalog identity')
    existing=next((row for row in before if row['id']==name),None)
    if existing is not None and existing['sha256']!=previous_sha:raise ValueError('exact previous owned package hash required')
    if existing is None and len(before)>=16:raise ValueError('catalog is full')
    others=[row for row in before if row['id']!=name]
    client.install(package);after=client.list_apps()
    expected=dict(id=name,title=manifest['title'],version=manifest['version'],sha256=hashlib.sha256(package).hexdigest())
    actual=next((row for row in after if row['id']==name),None)
    if (actual!=expected or len(after)!=len(others)+1 or
        sorted((row for row in after if row['id']!=name),key=lambda row:row['id'])!=sorted(others,key=lambda row:row['id'])):
        raise RuntimeError('catalog changed unexpectedly; stop without deleting or retrying')
    return actual
