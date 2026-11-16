"""Compare both VMs with an independent game oracle and a visible-board contract."""
import importlib
import json
from pathlib import Path
from .reference import Game
from .sdk import load_sdk
from .traces import traces


class EvaluationError(ValueError):
    def __init__(self,report):
        self.report=report
        super().__init__(json.dumps(report,sort_keys=True))


def required_draws(game):
    spec=game.spec;cell=min(280//spec['width'],160//spec['height'])
    rows=[[0,0,320,240,2113],[20,16,280,8,(31727,2047,2016,63488)[game.phase]]]
    for x,y in sorted(tuple(p) for p in spec['walls']):rows.append([21+x*cell,49+y*cell,cell-2,cell-2,27469])
    if spec['goal'] is not None:
        x,y=spec['goal'];rows.append([22+x*cell,50+y*cell,cell-4,cell-4,63519])
    for x,y in sorted(game.coins):rows.append([20+x*cell+cell//3,48+y*cell+cell//3,cell//3,cell//3,65504])
    if game.hazard is not None:
        x,y=game.hazard;rows.append([23+x*cell,51+y*cell,cell-6,cell-6,63488])
    rows.append([23+game.x*cell,51+game.y*cell,cell-6,cell-6,2016])
    if game.score:rows.append([20,224,280*game.score//spec['target'],6,65504])
    return rows


def _pixel(rows,x,y):
    result=None
    for rx,ry,w,h,color in rows:
        if rx<=x<rx+w and ry<=y<ry+h:result=color
    return result


def _drawing(actual,expected):
    if not 1<=len(actual)<=128:return False
    for row in actual:
        if (len(row)!=5 or any(type(v) is not int for v in row) or row[0]<0 or row[1]<0 or
            row[2]<=0 or row[3]<=0 or row[0]+row[2]>320 or row[1]+row[3]>240 or not 0<=row[4]<=65535):return False
    if actual[0]!=expected[0] or any(row not in actual for row in expected):return False
    # Ordering matters: drawing the required sprites and covering them afterward fails.
    for x,y,w,h,_ in expected[1:]:
        for px,py in ((x,y),(x+w-1,y),(x,y+h-1),(x+w-1,y+h-1),(x+w//2,y+h//2)):
            if _pixel(actual,px,py)!=_pixel(expected,px,py):return False
    return True


def evaluate(spec,manifest,blob,*,session_factory,native_runner,seed):
    total=0;captures={};summary={}
    for name,frames in traces(spec,seed=seed).items():
        session=None;index=-1
        try:
            native=native_runner([blob],frames,capabilities=1)
            if len(native)!=len(frames):raise EvaluationError(dict(trace=name,frame=-1,reason='native frame count'))
            session=session_factory(blob,manifest);game=Game(spec);now=0
            for index,((held,dt),row) in enumerate(zip(frames,native,strict=True)):
                now+=dt;expected_done=game.step(held,dt);actual_done=session.frame(held,now)
                if actual_done!=expected_done or row['status']!=('exit' if expected_done else 'running'):
                    raise EvaluationError(dict(trace=name,frame=index,reason='early/missing exit'))
                if not expected_done:
                    expected=game.snapshot()
                    actual={key:session.debug(export) for key,export in
                            (('value','debug_value'),('x','debug_x'),('y','debug_y'),('elapsed','debug_elapsed'))}
                    if actual!=expected or {key:row.get(key) for key in expected}!=expected:
                        raise EvaluationError(dict(trace=name,frame=index,reason='game state',expected=expected,actual=actual,native={key:row.get(key) for key in expected}))
                    drawing=[list(command) for command in session.commands]
                    if row['rects']!=drawing or not _drawing(drawing,required_draws(game)):
                        raise EvaluationError(dict(trace=name,frame=index,reason='drawing contract/VM mismatch'))
                    captures.setdefault(str(game.phase),drawing)
                total+=1
            if not session.closed:raise EvaluationError(dict(trace=name,frame=len(frames)-1,reason='resources not closed'))
            summary[name]=len(frames)
        except EvaluationError:raise
        except Exception as error:
            raise EvaluationError(dict(trace=name,frame=index,reason='VM/contract error',error_type=type(error).__name__)) from None
        finally:
            if session is not None:session.close()
    return dict(passed=True,both_vms_match=True,independent_oracle=True,frames=total,
                traces=summary,captures=captures,device_tested=False)


def check_build(spec,folder,sdk_root,*,seed):
    load_sdk(sdk_root);folder=Path(folder).resolve()
    sdk=importlib.import_module('labos.sdk');native=importlib.import_module('labos.native')
    package=importlib.import_module('labos.package')
    manifest,blob=package.decode((folder/'build/app.labapp').read_bytes())
    if any(manifest[key]!=spec[key] for key in ('id','title','version')) or manifest['capabilities']!=['draw']:
        raise EvaluationError(dict(trace='package',frame=-1,reason='trusted metadata mismatch'))
    runner=native.build_probe()
    return evaluate(spec,manifest,blob,session_factory=sdk.Session,
                    native_runner=lambda blobs,frames,capabilities:native.run_probe(runner,blobs,frames,capabilities=capabilities),seed=seed)
