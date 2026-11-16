import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from arcade_game_forge.samples import build_sample,load_sample

class SampleTests(unittest.TestCase):
    def test_three_bundled_sources_are_hash_checked_and_not_regenerated(self):
        for kind in ('maze','collect','dodge'):
            spec,source=load_sample(kind)
            self.assertEqual(spec['kind'],kind);self.assertIn('#include "lab_os.h"',source)
        with self.assertRaises(ValueError):load_sample('../foreign')

    def test_rebuild_uses_the_existing_ai_source_without_a_model_call(self):
        with tempfile.TemporaryDirectory() as tmp:
            out=Path(tmp)/'run'
            def fake_forge(*args,**kwargs):
                out.mkdir();return dict(accepted=True,attempts=[])
            with patch('arcade_game_forge.samples.forge',side_effect=fake_forge) as run:
                result=build_sample('maze',out,'sdk')
                self.assertEqual(result['origin'],'bundled_sample_rebuild')
                self.assertEqual(run.call_args.kwargs['generator']('ignored',None),load_sample('maze')[1])
