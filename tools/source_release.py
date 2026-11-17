"""検査済みmainのタグからsource archiveを作る。ネット送信/実機操作は行わない。"""
import argparse,gzip,hashlib,io,re,subprocess,tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
PRIVATE={'backups','secrets','reports','logs','downloads','build','dist','runs','datasets','checkpoints',
         '__pycache__','.cache','.venv','.git'}
BINARY={'.bin','.elf','.map','.wasm','.labapp','.mpy','.uf2','.wav','.pcm','.mp3','.key','.pem',
        '.onnx','.pt','.ckpt','.safetensors'}
TOKEN=re.compile(rb'(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{30,}|-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----)')


def check_paths(root,paths):
    root=Path(root).resolve()
    if 'LICENSE' not in paths:raise ValueError('source license required')
    for name in paths:
        rel=Path(name);path=root/rel
        if (rel.is_absolute() or '..' in rel.parts or '\\' in name or
            any(p in PRIVATE for p in rel.parts) or rel.name.startswith('.env') and rel.name!='.env.example' or
            rel.suffix in BINARY or name=='app/desk_key.h'):
            raise ValueError('private/generated publication path: '+name)
        if not path.is_file() or path.resolve()!=path.absolute():raise ValueError('regular publication file required: '+name)
        data=path.read_bytes()
        if TOKEN.search(data) or re.search(rb'/Users/[A-Za-z0-9_.-]+/',data):
            raise ValueError('private content in source: '+name)
        media=rel.parts[:2]==('docs','media') and rel.suffix in {'.png','.gif','.mp4'}
        model=rel.parts[:1]==('models',) and rel.suffix=='.npz'
        if not media and not model:data.decode('utf-8')
    return len(paths)


def create_release(root,tag,output):
    root=Path(root).resolve()
    if not re.fullmatch(r'v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)',tag):raise ValueError('semantic vMAJOR.MINOR.PATCH tag required')
    project=tomllib.loads((root/'pyproject.toml').read_text())['project'];name=project['name'];version=project['version']
    if not re.fullmatch(r'[a-z][a-z0-9-]{0,62}',name) or tag!='v'+version:raise ValueError('release name/version mismatch')
    def git(*args):return subprocess.check_output(['git','-C',str(root),*args],stderr=subprocess.DEVNULL)
    if git('status','--porcelain').strip():raise ValueError('clean release checkout required')
    try:
        if git('rev-parse','--verify',f'refs/tags/{tag}^{{commit}}').strip()!=git('rev-parse','HEAD').strip():
            raise ValueError('release tag must identify HEAD')
        git('merge-base','--is-ancestor','HEAD','refs/remotes/origin/main')
    except subprocess.CalledProcessError as exc:raise ValueError('tagged main commit required') from exc
    paths=[p for p in git('ls-files','-z').decode().split('\0') if p];check_paths(root,paths)
    output=Path(output).absolute()
    if (not output.is_relative_to(root/'dist') or '..' in output.parts or
        any(p.is_symlink() for p in (output,*output.parents)) or output.exists()):
        raise ValueError('fresh real output below dist required')
    archive=git('archive','--format=tar','--prefix='+name+'-'+version+'/','HEAD')
    compressed=io.BytesIO()
    with gzip.GzipFile(fileobj=compressed,filename='',mode='wb',mtime=0) as stream:stream.write(archive)
    data=compressed.getvalue();output.mkdir(parents=True)
    target=output/(name+'-'+version+'-source.tar.gz');target.write_bytes(data)
    (output/'SHA256SUMS').write_text(hashlib.sha256(data).hexdigest()+'  '+target.name+'\n')
    return target


def main(argv=None):
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tag',required=True)
    args=parser.parse_args(argv);result=create_release(ROOT,args.tag,ROOT/'dist/source-release')
    print(result.relative_to(ROOT));return 0


if __name__=='__main__':raise SystemExit(main())
