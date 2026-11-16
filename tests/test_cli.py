import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fixtures import spec
from arcade_game_forge.cli import main

class CliTests(unittest.TestCase):
    def test_validation_and_generation_result_use_real_exit_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            value=Path(tmp)/'spec.json';value.write_text(json.dumps(spec()))
            out=io.StringIO();self.assertEqual(main(['validate',str(value)],out=out),0)
            for accepted,code in ((True,0),(False,1)):
                with patch('arcade_game_forge.cli.forge',return_value=dict(accepted=accepted)) as run:
                    self.assertEqual(main(['make',str(value),'--sdk','sdk','--output',str(Path(tmp)/'run')],out=out),code)
                    self.assertEqual(run.call_args.args[0],spec())

    def test_invalid_spec_or_timeout_does_not_start_generation(self):
        with tempfile.TemporaryDirectory() as tmp:
            value=Path(tmp)/'bad.json';value.write_text('{broken')
            with patch('arcade_game_forge.cli.forge') as run:
                self.assertEqual(main(['make',str(value),'--sdk','sdk','--output',str(Path(tmp)/'run')],out=io.StringIO()),2)
                value.write_text(json.dumps(spec()))
                self.assertEqual(main(['make',str(value),'--sdk','sdk','--output',str(Path(tmp)/'run'),'--timeout','nan'],out=io.StringIO()),2)
                run.assert_not_called()
