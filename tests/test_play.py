import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from fixtures import spec
from arcade_game_forge.play import ready_package,play

class PlayTests(unittest.TestCase):
    def fixture(self,root):
        (root/'attempt-1/game/build').mkdir(parents=True)
        package=b'fixture package';(root/'attempt-1/game/build/app.labapp').write_bytes(package)
        value=spec();(root/'spec.json').write_text(json.dumps(value))
        result=dict(accepted=True,status='finished',spec_sha256=hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest(),
                    ready=dict(folder='attempt-1/game',passed=True,package_sha256=hashlib.sha256(package).hexdigest()))
        (root/'result.json').write_text(json.dumps(result));return result

    def test_only_the_accepted_unchanged_run_package_is_selected(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);result=self.fixture(root)
            value,package=ready_package(root)
            self.assertEqual(value,spec());self.assertEqual(package,b'fixture package')
            (root/'attempt-1/game/build/app.labapp').write_bytes(b'changed')
            with self.assertRaises(ValueError):ready_package(root)

    def test_failed_run_traversal_and_changed_spec_do_not_start_a_window(self):
        for mode in ('rejected','traversal','spec'):
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp);result=self.fixture(root)
                if mode=='rejected':result['accepted']=False
                if mode=='traversal':result['ready']['folder']='../foreign'
                if mode=='spec':(root/'spec.json').write_text(json.dumps(dict(spec(),title='Different')))
                (root/'result.json').write_text(json.dumps(result))
                with self.assertRaises(ValueError):ready_package(root)
        with self.assertRaises(ValueError):play('/unused','/unused',max_frames=True)
