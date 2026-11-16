"""Create a tested WASM game from a closed JSON specification."""
import argparse
import json
from pathlib import Path
import sys
from .deploy import install_run
from .evaluate import check_build
from .generator import CodexGenerator
from .pipeline import forge
from .play import play
from .samples import build_sample
from .media import render_run
from .spec import validate


def main(argv=None,*,out=None):
    out=out or sys.stdout
    parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='action',required=True)
    for action in ('validate','make','check'):
        child=sub.add_parser(action);child.add_argument('spec',type=Path)
        if action!='validate':child.add_argument('--sdk',required=True)
        if action=='make':
            child.add_argument('--output',required=True,type=Path)
            child.add_argument('--attempts',type=int,default=3);child.add_argument('--timeout',type=float,default=180)
        if action=='check':
            child.add_argument('--game',required=True,type=Path);child.add_argument('--seed',type=int,default=7001)
    player=sub.add_parser('play');player.add_argument('run',type=Path)
    player.add_argument('--sdk',required=True);player.add_argument('--frames',type=int)
    sample=sub.add_parser('sample');sample.add_argument('kind',choices=('maze','collect','dodge'))
    sample.add_argument('--sdk',required=True);sample.add_argument('--output',required=True,type=Path)
    renderer=sub.add_parser('render');renderer.add_argument('run',type=Path)
    renderer.add_argument('--sdk',required=True);renderer.add_argument('--output',required=True,type=Path)
    installer=sub.add_parser('install');installer.add_argument('run',type=Path)
    installer.add_argument('--sdk',required=True);installer.add_argument('--port',required=True)
    installer.add_argument('--previous-sha')
    args=parser.parse_args(argv)
    try:
        if args.action=='install':
            result=install_run(args.run,args.sdk,args.port,previous_sha=args.previous_sha)
            print(json.dumps(result),file=out);return 0
        if args.action=='render':
            result=render_run(args.run,args.sdk,args.output)
            print(json.dumps(result),file=out);return 0
        if args.action=='play':
            result=play(args.run,args.sdk,max_frames=args.frames)
            print(json.dumps(result),file=out);return 0
        if args.action=='sample':
            result=build_sample(args.kind,args.output,args.sdk)
            print(json.dumps(result),file=out);return 0 if result['accepted'] else 1
        if args.spec.stat().st_size>16384:raise ValueError('spec file too large')
        spec=validate(json.loads(args.spec.read_text()))
        if args.action=='validate':result=dict(valid=True,id=spec['id'])
        elif args.action=='make':
            generator=CodexGenerator(timeout=args.timeout)
            result=forge(spec,args.output,args.sdk,generator=generator,max_attempts=args.attempts)
        else:result=check_build(spec,args.game,args.sdk,seed=args.seed)
        print(json.dumps(result,ensure_ascii=False),file=out)
        return 1 if result.get('accepted') is False else 0
    except (OSError,ValueError,RuntimeError) as error:
        print(json.dumps(dict(error_type=type(error).__name__,message='Input, generator, build or evaluation failed; inspect the local run report.')),file=out)
        return 2


if __name__=='__main__':raise SystemExit(main())
