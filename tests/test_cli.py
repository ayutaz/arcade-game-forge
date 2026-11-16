import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from fixtures import spec
from arcade_game_forge.cli import main

class CliTests(unittest.TestCase):
    def test_install_requires_explicit_port_and_passes_the_previous_owned_hash(self):
        with patch('arcade_game_forge.cli.install_run',return_value=dict(id='forge-maze'),create=True) as install:
            self.assertEqual(main(['install','runs/accepted','--sdk','sdk','--port','port','--previous-sha','a'*64],out=io.StringIO()),0)
            self.assertEqual(install.call_args.kwargs['previous_sha'],'a'*64)

    def test_render_uses_an_accepted_run_without_generation(self):
        with patch('arcade_game_forge.cli.render_run',return_value=dict(source='host replay'),create=True) as render:
            self.assertEqual(main(['render','runs/example','--sdk','sdk','--output','images/new'],out=io.StringIO()),0)
            self.assertEqual(render.call_args.args[0],Path('runs/example'))
    def test_sample_rebuild_does_not_require_generation(self):
        with patch('arcade_game_forge.cli.build_sample',return_value=dict(accepted=True),create=True) as sample:
            self.assertEqual(main(['sample','maze','--sdk','sdk','--output','runs/sample'],out=io.StringIO()),0)
            self.assertEqual(sample.call_args.args[0],'maze')
    def test_play_uses_the_fixed_run_without_generation(self):
        with patch('arcade_game_forge.cli.play',return_value=dict(frames=12,device_tested=False),create=True) as window:
            self.assertEqual(main(['play','runs/example','--sdk','sdk','--frames','12'],out=io.StringIO()),0)
            self.assertEqual(window.call_args.kwargs['max_frames'],12)

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
