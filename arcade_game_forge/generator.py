"""Bounded local Codex integration; no API key or paid-provider fallback."""
import json
import math
import os
from pathlib import Path
import signal
import subprocess
import time
from .source import parse_response


class GeneratorError(RuntimeError):pass


class CodexGenerator:
    def __init__(self,*,command=None,timeout=180,max_bytes=1048576):
        self.command=['codex'] if command is None else list(command)
        if (not self.command or any(type(arg) is not str or not arg or '\0' in arg for arg in self.command) or
            type(timeout) not in (int,float) or not math.isfinite(timeout) or not .05<=timeout<=600 or
            type(max_bytes) is not int or not 1024<=max_bytes<=4194304):raise ValueError('generator resource bounds')
        self.timeout=timeout;self.max_bytes=max_bytes

    def __call__(self,prompt,workspace):
        if type(prompt) is not str or not 1<=len(prompt.encode())<=65536:raise ValueError('bounded generation prompt required')
        workspace=Path(workspace).absolute()
        if workspace.is_symlink():raise ValueError('real generation workspace required')
        workspace=workspace.parent.resolve()/workspace.name
        if workspace.exists():raise ValueError('fresh generation workspace required')
        # Authentication stays with the CLI. Do not forward API credentials into this run.
        env={key:value for key,value in os.environ.items() if not any(word in key.upper() for word in
             ('API_KEY','TOKEN','SECRET','PASSWORD')) and not key.startswith(('OPENAI_','ANTHROPIC_','VAST_','HF_','GH_','GITHUB_'))}
        try:
            status=subprocess.run([*self.command,'login','status'],stdin=subprocess.DEVNULL,capture_output=True,
                                  timeout=10,env=env)
        except (OSError,subprocess.TimeoutExpired):raise GeneratorError('local Codex authentication unavailable') from None
        if status.returncode or b'Logged in using ChatGPT' not in status.stdout+status.stderr:
            raise GeneratorError('existing ChatGPT CLI login required; API billing is disabled')
        workspace.mkdir(parents=True,mode=0o700)
        subprocess.run(['git','init','--quiet','-b','main',str(workspace)],check=True,timeout=10,env=env)
        request=workspace/'request.txt';request.write_text(prompt)
        schema=workspace/'response-schema.json'
        schema.write_text(json.dumps(dict(type='object',properties=dict(app_c=dict(type='string')),
                                         required=['app_c'],additionalProperties=False)))
        response=workspace/'response.json';events=workspace/'events.jsonl';errors=workspace/'stderr.log'
        args=[*self.command,'exec','--sandbox','read-only','--ephemeral','--json',
              '-c','approval_policy="never"','-c','model_provider="openai"',
              '--output-schema',str(schema),'-o',str(response),'-C',str(workspace),'-']
        started=time.monotonic();process=None
        def terminate():
            if process is not None and process.poll() is None:
                try:os.killpg(process.pid,signal.SIGTERM)
                except ProcessLookupError:pass
                try:process.wait(timeout=.3)
                except subprocess.TimeoutExpired:
                    try:os.killpg(process.pid,signal.SIGKILL)
                    except ProcessLookupError:pass
                    process.wait(timeout=2)
        try:
            with request.open('rb') as stdin,events.open('wb') as stdout,errors.open('wb') as stderr:
                process=subprocess.Popen(args,stdin=stdin,stdout=stdout,stderr=stderr,env=env,
                                         cwd=workspace,start_new_session=True)
                while process.poll() is None:
                    if time.monotonic()-started>self.timeout:raise GeneratorError('generation deadline exceeded')
                    if sum(p.stat().st_size for p in (events,errors,response) if p.exists())>self.max_bytes:
                        raise GeneratorError('generation output budget exceeded')
                    time.sleep(.01)
            if process.returncode:raise GeneratorError('local generator exited unsuccessfully')
            if sum(p.stat().st_size for p in (events,errors,response) if p.exists())>self.max_bytes:
                raise GeneratorError('generation output budget exceeded')
            for line in events.read_text().splitlines():
                row=json.loads(line)
                if row.get('type') in ('item.started','item.completed'):
                    if row.get('item',{}).get('type') not in ('agent_message','reasoning'):
                        raise GeneratorError('code generation used a tool; inspect the private run')
            return parse_response(response.read_text())
        except (OSError,ValueError) as error:
            raise GeneratorError('invalid or unavailable structured generator output') from error
        except KeyboardInterrupt:
            raise GeneratorError('generation cancelled') from None
        finally:terminate()
