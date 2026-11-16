import json
from pathlib import Path
import sys
import tempfile
import unittest
from arcade_game_forge.generator import CodexGenerator, GeneratorError

GOOD='#include "lab_os.h"\nint f(void){return 1;}\n'

class GeneratorTests(unittest.TestCase):
    def fake(self,base,mode):
        script=base/'cli.py'
        script.write_text('''import json,os,pathlib,sys,time
if sys.argv[1:]==['login','status']:
 print('Logged in using ChatGPT');raise SystemExit(0)
assert '--sandbox' in sys.argv and sys.argv[sys.argv.index('--sandbox')+1]=='read-only'
assert '--ephemeral' in sys.argv
assert not any('dangerously' in arg or arg=='--trust' for arg in sys.argv)
assert 'OPENAI_API_KEY' not in os.environ
assert 'do not use tools' in sys.stdin.read().lower()
mode='''+repr(mode)+'''
if mode=='timeout':time.sleep(10)
if mode=='flood':print('x'*10000);raise SystemExit(0)
if mode=='fail':print('sensitive stderr',file=sys.stderr);raise SystemExit(9)
path=pathlib.Path(sys.argv[sys.argv.index('-o')+1]);path.write_text(json.dumps({'app_c':'''+repr(GOOD)+'''}))
print(json.dumps({'type':'turn.completed','usage':{'input_tokens':12,'output_tokens':8}}))
''')
        return [sys.executable,str(script)]

    def test_real_subprocess_sandbox_structured_result_and_private_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp);generator=CodexGenerator(command=self.fake(base,'success'),timeout=2)
            self.assertEqual(generator('Do not use tools. Return JSON.',base/'work'),GOOD)
            self.assertEqual((base/'work').stat().st_mode&0o777,0o700)
            with self.assertRaises(ValueError):generator('Do not use tools.',base/'work')

    def test_timeout_output_limit_and_exit_failure_are_reported_without_echoing_stderr(self):
        for mode in ('timeout','flood','fail'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                base=Path(tmp);generator=CodexGenerator(command=self.fake(base,mode),timeout=.1,max_bytes=2048)
                with self.assertRaises(GeneratorError) as caught:generator('Do not use tools.',base/'work')
                self.assertNotIn('sensitive',str(caught.exception))

    def test_bad_parameters_create_no_workspace(self):
        with tempfile.TemporaryDirectory() as tmp:
            base=Path(tmp)
            for deadline in (0,float('nan'),601):
                with self.assertRaises(ValueError):CodexGenerator(timeout=deadline)
            generator=CodexGenerator(command=self.fake(base,'success'))
            with self.assertRaises(ValueError):generator('x'*65537,base/'work')
            self.assertFalse((base/'work').exists())
