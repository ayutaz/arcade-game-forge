import unittest
from fixtures import spec
from arcade_game_forge.reference import Game
from arcade_game_forge.traces import traces

class TraceTests(unittest.TestCase):
    def test_each_game_has_win_reset_input_edges_and_normal_exit(self):
        for kind in ('maze','dodge','collect'):
            rows=traces(spec(kind),seed=987)
            self.assertEqual(rows,traces(spec(kind),seed=987))
            self.assertIn('victory',rows);self.assertIn('random',rows)
            for name,frames in rows.items():
                game=Game(spec(kind));won=False;done=False
                self.assertLessEqual(len(frames),600)
                for index,(key,dt) in enumerate(frames):
                    done=game.step(key,dt);won|=game.phase==2
                    if done:self.assertEqual(index,len(frames)-1)
                self.assertTrue(done,(kind,name))
                if name=='victory':self.assertTrue(won,kind)

    def test_different_seeds_change_only_the_random_evaluation_inputs(self):
        a=traces(spec(),seed=1);b=traces(spec(),seed=2)
        self.assertNotEqual(a['random'],b['random'])
        self.assertEqual(a['victory'],b['victory'])
