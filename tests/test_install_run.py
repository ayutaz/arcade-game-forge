from contextlib import contextmanager
import hashlib
from pathlib import Path
import unittest
from unittest.mock import patch
from test_deploy import Client,PACKAGE,HASH
from arcade_game_forge.deploy import install_run

class InstallRunTests(unittest.TestCase):
    def test_accepted_fixed_package_adds_only_owned_app_and_closes_connection(self):
        events=[];client=Client()
        manifest=dict(id='forge-maze',title='Forge Maze',version='1.0.0',capabilities=['draw'])
        @contextmanager
        def connect(port):
            events.append('open')
            try:yield client
            finally:events.append('close')
        with patch('arcade_game_forge.deploy.ready_package',return_value=(dict(manifest),PACKAGE)),patch('arcade_game_forge.deploy.transport',return_value=(lambda _: (manifest,b''),connect)):
            result=install_run('runs/accepted','sdk','explicit-port')
            self.assertEqual(result['sha256'],HASH)
            with self.assertRaises(ValueError):install_run('runs/accepted','sdk','explicit-port')
        self.assertEqual(events,['open','close','open','close']);self.assertEqual(client.writes,1)
    def test_bad_run_or_changed_metadata_never_opens_port(self):
        with patch('arcade_game_forge.deploy.ready_package',side_effect=ValueError()),patch('arcade_game_forge.deploy.transport') as adapter:
            with self.assertRaises(ValueError):install_run('bad','sdk','port')
            adapter.assert_not_called()
        with patch('arcade_game_forge.deploy.ready_package',return_value=(dict(id='forge-maze',title='expected',version='1.0.0'),PACKAGE)),patch('arcade_game_forge.deploy.transport',return_value=(lambda _: (dict(id='forge-maze',title='changed',version='1.0.0',capabilities=['draw']),b''),lambda _:self.fail('port opened'))):
            with self.assertRaises(ValueError):install_run('changed','sdk','port')
