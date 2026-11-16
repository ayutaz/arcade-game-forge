from pathlib import Path
import tempfile
import unittest
from fixtures import spec
from arcade_game_forge.evaluate import EvaluationError
from arcade_game_forge.pipeline import forge

GOOD='#include "lab_os.h"\nint f(void){return 1;}\n'

class PipelineTests(unittest.TestCase):
    def services(self,*,first_bad=False,nondeterministic=False):
        prompts=[];builds=[];checks=[]
        def generate(prompt,workspace):prompts.append(prompt);return GOOD
        def build(value,source,folder,sdk):
            builds.append(folder);folder.mkdir(parents=True)
            (folder/'app.c').write_text(source)
            return dict(package_sha256=('b' if nondeterministic and len(builds)>1 else 'a')*64,
                        package_bytes=1234,device_tested=False)
        def check(value,folder,sdk,*,seed):
            checks.append(folder)
            if first_bad and len(checks)==1:raise EvaluationError(dict(trace='random',frame=7,reason='game state',expected=dict(x=3),actual=dict(x=2)))
            return dict(passed=True,both_vms_match=True,independent_oracle=True,frames=200,device_tested=False,captures={})
        return generate,build,check,prompts,builds

    def test_first_failure_is_preserved_and_diagnostics_drive_next_attempt(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate,build,check,prompts,builds=self.services(first_bad=True)
            result=forge(spec(),Path(tmp)/'run','unused-sdk',generator=generate,builder=build,evaluator=check,eval_seed=99,max_attempts=3)
            self.assertTrue(result['accepted']);self.assertEqual(len(result['attempts']),2)
            self.assertFalse(result['attempts'][0]['passed']);self.assertTrue(result['attempts'][1]['passed'])
            self.assertIn('game state',prompts[1]);self.assertNotIn('evaluation_seed',prompts[1])
            self.assertNotIn('Game.step',prompts[0]);self.assertEqual(len(builds),3)
            self.assertFalse(result['device_tested']);self.assertTrue((Path(tmp)/'run/result.json').is_file())

    def test_failed_reproduction_is_not_a_ready_package(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate,build,check,_,_=self.services(nondeterministic=True)
            result=forge(spec(),Path(tmp)/'run','sdk',generator=generate,builder=build,evaluator=check,max_attempts=1)
            self.assertFalse(result['accepted']);self.assertNotIn('ready',result)
            self.assertIn('deterministic',str(result['attempts']))

    def test_invalid_spec_existing_output_and_bounds_do_not_call_model(self):
        with tempfile.TemporaryDirectory() as tmp:
            generate,build,check,prompts,_=self.services();base=Path(tmp)
            for value,out,attempts in ((dict(spec(),width=True),base/'out',3),(spec(),base,3),(spec(),base/'out',6)):
                with self.assertRaises(ValueError):forge(value,out,'sdk',generator=generate,builder=build,evaluator=check,max_attempts=attempts)
            self.assertEqual(prompts,[])
