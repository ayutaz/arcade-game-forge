import os
from pathlib import Path
import tempfile
import unittest
from arcade_game_forge.samples import load_sample
from arcade_game_forge.sdk import build_game
from arcade_game_forge.evaluate import check_build

ROOT=Path(__file__).resolve().parents[2]
SDK=Path(os.environ.get('ARCADE_OS_ROOT',str(ROOT.parent/'scratch-arcade-os')))

class GeneratedSampleTests(unittest.TestCase):
    def test_three_real_ai_games_rebuild_and_pass_a_second_evaluation_seed(self):
        with tempfile.TemporaryDirectory() as tmp:
            for kind in ('maze','collect','dodge'):
                with self.subTest(kind=kind):
                    spec,source=load_sample(kind);folder=Path(tmp)/kind
                    built=build_game(spec,source,folder,SDK)
                    result=check_build(spec,folder,SDK,seed=947315)
                    self.assertTrue(result['passed']);self.assertTrue(result['both_vms_match'])
                    self.assertLessEqual(built['package_bytes'],16384)
