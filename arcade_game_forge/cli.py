"""Create a tested WASM game from a closed JSON specification."""
import argparse
import json
from pathlib import Path
import sys
from .evaluate import check_build
from .generator import CodexGenerator
from .pipeline import forge
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
    args=parser.parse_args(argv)
    try:
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
