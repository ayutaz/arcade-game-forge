import os
from pathlib import Path
import tempfile
import unittest
from arcade_game_forge.sdk import build_game, load_sdk

ROOT=Path(__file__).resolve().parents[2]
SDK=Path(os.environ.get('ARCADE_OS_ROOT',str(ROOT.parent/'scratch-arcade-os')))
SOURCE='''#include "lab_os.h"
uint32_t sdk_abi(void){return LAB_ABI;}
void init(void){}
void shutdown(uint32_t reason){(void)reason;}
int32_t debug_value(void){return 0;}
int32_t debug_x(void){return 0;}
int32_t debug_y(void){return 0;}
int32_t debug_elapsed(void){return 0;}
int32_t tick(uint32_t h,uint32_t p,uint32_t r,uint32_t dt){
 (void)h;(void)r;(void)dt;if(p&BACK)return 1;rect(0,0,320,240,2113);return 0;}
'''

def specification():
    return dict(schema=1,kind='maze',id='forge-maze',title='Forge Maze',version='1.0.0',
       width=6,height=6,start=[0,0],walls=[[1,0]],goal=[2,0],coins=[],target=1,
       step_ms=500,duration_ms=60000,seed=1)

class SdkTests(unittest.TestCase):
    def test_real_build_is_deterministic_draw_only_and_bounded(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=build_game(specification(),SOURCE,Path(tmp)/'a',SDK)
            b=build_game(specification(),SOURCE,Path(tmp)/'b',SDK)
            self.assertEqual(a['package_sha256'],b['package_sha256'])
            self.assertLessEqual(a['package_bytes'],16384)
            self.assertEqual(a['capabilities'],['draw']);self.assertFalse(a['device_tested'])
            with self.assertRaises(ValueError):build_game(specification(),SOURCE,Path(tmp)/'a',SDK)

    def test_unsafe_source_or_foreign_sdk_creates_no_game_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'never-created'
            with self.assertRaises(ValueError):build_game(specification(),'#include "/tmp/foreign"',output,SDK)
            self.assertFalse(output.exists())
            with self.assertRaises(ValueError):load_sdk(Path(tmp))

    def test_both_real_vms_still_fail_an_incorrect_game(self):
        from arcade_game_forge.evaluate import check_build, EvaluationError
        with tempfile.TemporaryDirectory() as tmp:
            build_game(specification(),SOURCE,Path(tmp)/'incorrect',SDK)
            with self.assertRaises(EvaluationError):check_build(specification(),Path(tmp)/'incorrect',SDK,seed=7)
