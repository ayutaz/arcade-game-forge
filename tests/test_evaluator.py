import unittest
from fixtures import spec
from arcade_game_forge.reference import Game
from arcade_game_forge.evaluate import evaluate, required_draws, EvaluationError


class EvaluatorTests(unittest.TestCase):
    def bindings(self,value,*,wrong=False,blank=False,mismatch=False):
        class Session:
            def __init__(self,*args):self.game=Game(value);self.now=0;self.closed=False;self.commands=[]
            def frame(self,key,now):
                done=self.game.step(key,now-self.now);self.now=now
                self.commands=[] if blank else required_draws(self.game)
                if done:self.closed=True
                return done
            def debug(self,name):
                key={'debug_value':'value','debug_x':'x','debug_y':'y','debug_elapsed':'elapsed'}[name]
                return self.game.snapshot()[key]+(1 if wrong and key=='value' else 0)
            def close(self):self.closed=True
        def native(blobs,frames,*,capabilities):
            game=Game(value);rows=[]
            for key,dt in frames:
                done=game.step(key,dt)
                row=dict(status='exit' if done else 'running',rects=[] if blank else required_draws(game),**game.snapshot())
                if wrong:row['value']+=1
                if mismatch:row['x']+=1
                rows.append(row)
            return rows
        return Session,native

    def test_three_games_pass_both_vm_and_independent_trace_contracts(self):
        for kind in ('maze','collect','dodge'):
            value=spec(kind);session,native=self.bindings(value)
            result=evaluate(value,{},b'fixture',session_factory=session,native_runner=native,seed=72)
            self.assertTrue(result['passed']);self.assertTrue(result['both_vms_match'])
            self.assertGreater(result['frames'],100);self.assertFalse(result['device_tested'])

    def test_matching_vms_cannot_hide_wrong_game_state_or_blank_drawing(self):
        for options in (dict(wrong=True),dict(blank=True),dict(mismatch=True)):
            value=spec();session,native=self.bindings(value,**options)
            with self.assertRaises(EvaluationError) as caught:
                evaluate(value,{},b'fixture',session_factory=session,native_runner=native,seed=2)
            self.assertIn('trace',caught.exception.report)
            self.assertIn('frame',caught.exception.report)

    def test_renderer_contract_has_visible_player_goal_walls_and_phase(self):
        game=Game(spec());rects=required_draws(game)
        self.assertIn([23,51,20,20,2016],rects)
        self.assertIn([47,49,24,24,27469],rects)
        self.assertEqual(rects[0],[0,0,320,240,2113])
        self.assertLess(len(rects),128)
