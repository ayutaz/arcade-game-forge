import os
from pathlib import Path
import tempfile
import unittest
from PIL import Image
from arcade_game_forge.samples import build_sample
from arcade_game_forge.media import render_run

ROOT=Path(__file__).resolve().parents[2]
SDK=Path(os.environ.get('ARCADE_OS_ROOT',str(ROOT.parent/'scratch-arcade-os')))

class MediaTests(unittest.TestCase):
    def test_real_game_images_cover_title_play_and_win_without_claiming_device_capture(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);build_sample('maze',root/'run',SDK)
            result=render_run(root/'run',SDK,root/'images')
            self.assertEqual(result['source'],'deterministic host WASM replay')
            self.assertFalse(result['device_capture']);self.assertIn('2',result['screens'])
            with Image.open(root/'images/phase-1.png') as image:
                self.assertEqual(image.size,(320,240));self.assertEqual(image.convert('RGB').getpixel((25,55)),(0,255,0))
            with Image.open(root/'images/replay.gif') as image:self.assertGreater(image.n_frames,1)
            with self.assertRaises(ValueError):render_run(root/'run',SDK,root/'images')
