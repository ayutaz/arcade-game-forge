import unittest
from fixtures import spec
from arcade_game_forge.reference import Game


class ReferenceTests(unittest.TestCase):
    def press(self,game,mask,dt=20):
        game.step(0,0);return game.step(mask,dt)
    def test_maze_wall_win_reset_and_back_are_independent_of_rendering(self):
        game=Game(spec());game.step(0,1000);self.assertEqual(game.elapsed,0)
        self.press(game,16);self.assertEqual(game.phase,1);self.assertEqual(game.elapsed,0)
        self.press(game,1);self.assertEqual((game.x,game.y),(0,0))
        for key in (4,1,1,8):self.press(game,key)
        self.assertEqual((game.x,game.y,game.phase,game.score),(2,0,2,1))
        before=game.snapshot();game.step(0,1000);self.assertEqual(game.snapshot(),before)
        self.assertTrue(self.press(game,192));self.assertEqual(game.snapshot(),before)
        self.press(game,32);self.assertEqual((game.phase,game.elapsed,game.score),(0,0,0))

    def test_collect_counts_each_coin_once_and_restarts_cleanly(self):
        game=Game(spec('collect'));self.press(game,16);self.press(game,4)
        self.assertEqual(game.score,1)
        self.press(game,8);self.press(game,4);self.assertEqual(game.score,1)
        self.press(game,1);self.assertEqual((game.score,game.phase),(2,2))
        self.press(game,32);self.press(game,16);self.press(game,4);self.assertEqual(game.score,1)

    def test_dodge_fixed_seed_collision_win_and_large_step(self):
        value=spec('dodge');game=Game(value);self.press(game,16);game.step(0,500)
        self.assertEqual(game.hazard,(0,0))
        self.press(game,2,0);game.step(0,2500);self.assertEqual(game.phase,3)
        game=Game(value);self.press(game,16);game.step(0,3500)
        self.assertEqual((game.phase,game.score),(2,1))
        game=Game(value);self.press(game,16);game.step(0,60000)
        self.assertEqual((game.phase,game.score,game.elapsed),(3,0,60000))

    def test_input_edge_and_deadline_contract(self):
        value=spec();value['walls']=[];game=Game(value)
        game.step(16,10);game.step(1,10);game.step(1,10)
        self.assertEqual(game.x,1)
        game.step(0,59980);self.assertEqual(game.phase,3)
        for key,dt in ((256,0),(0,-1),(0,60001),(True,0)):
            with self.assertRaises(ValueError):game.step(key,dt)
