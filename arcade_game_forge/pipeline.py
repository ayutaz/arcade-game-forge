"""Generate, test, repair and reproduce a package without touching a device."""
import hashlib
import json
import os
from pathlib import Path
import secrets
from .evaluate import EvaluationError,check_build
from .generator import CodexGenerator,GeneratorError
from .sdk import SDK_COMMIT,build_game
from .source import check_source
from .spec import validate

ROOT=Path(__file__).resolve().parents[1]


def _write(path,value):
    temporary=path.with_suffix('.tmp')
    temporary.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n');os.replace(temporary,path)


def forge(spec,output,sdk_root,*,generator=None,builder=build_game,evaluator=check_build,
          max_attempts=3,eval_seed=None):
    spec=validate(spec)
    if type(max_attempts) is not int or not 1<=max_attempts<=5:raise ValueError('one to five attempts required')
    if eval_seed is None:eval_seed=secrets.randbelow(2147483648)
    if type(eval_seed) is not int or not 0<=eval_seed<=2147483647:raise ValueError('evaluation seed')
    output=Path(output).absolute()
    if output.is_symlink():raise ValueError('real run output required')
    output=output.parent.resolve()/output.name
    if output.exists():raise ValueError('fresh run directory required')
    generator=generator or CodexGenerator()
    contract=(ROOT/'prompts/game-contract.txt').read_text()
    base_prompt=contract+'\n'+json.dumps(spec,sort_keys=True)+'\n'
    output.mkdir(parents=True,mode=0o700)
    _write(output/'spec.json',spec)
    result=dict(accepted=False,status='running',attempts=[],evaluation_seed=eval_seed,sdk_commit=SDK_COMMIT,
                spec_sha256=hashlib.sha256(json.dumps(spec,sort_keys=True).encode()).hexdigest(),device_tested=False)
    _write(output/'result.json',result)
    last_source='';failure=None
    for attempt in range(1,max_attempts+1):
        folder=output/f'attempt-{attempt}';folder.mkdir()
        prompt=base_prompt
        if failure is not None:
            prompt+='\nYour previous implementation failed independent checks. Correct it; do not change the contract.\n'
            prompt+=json.dumps(failure,sort_keys=True)[:8000]+'\nPrevious C (possibly truncated):\n'+last_source[:32000]
        item=dict(attempt=attempt,passed=False)
        try:
            source=check_source(generator(prompt,folder/'generator'));last_source=source
            built=builder(spec,source,folder/'game',sdk_root)
            evaluation=evaluator(spec,folder/'game',sdk_root,seed=eval_seed)
            if evaluation.get('passed') is not True:raise ValueError('independent evaluation did not pass')
            reproduced=builder(spec,source,folder/'reproduction',sdk_root)
            if built['package_sha256']!=reproduced['package_sha256']:
                raise ValueError('deterministic reproduction failed')
            item.update(passed=True,source_sha256=hashlib.sha256(source.encode()).hexdigest(),
                        package_sha256=built['package_sha256'],package_bytes=built['package_bytes'])
            _write(folder/'evaluation.json',evaluation)
            result.update(accepted=True,ready=dict(folder=str((folder/'game').relative_to(output)),**item))
        except (ValueError,RuntimeError,OSError) as error:
            failure=error.report if isinstance(error,EvaluationError) else dict(reason=str(error)[:8000],error_type=type(error).__name__)
            # Local compiler paths are unnecessary for model diagnostics or public reports.
            failure=json.loads(json.dumps(failure).replace(str(output),'${RUN}').replace(str(sdk_root),'${SDK}'))
            item['failure']=failure;_write(folder/'failure.json',failure)
        result['attempts'].append(item);_write(output/'result.json',result)
        if result['accepted']:break
    result['status']='finished';_write(output/'result.json',result)
    return result
