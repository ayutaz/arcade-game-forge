import copy
import unittest
from fixtures import spec
from arcade_game_forge.spec import validate


class SpecTests(unittest.TestCase):
    def test_three_games_validate_without_mutating_input(self):
        for kind in ('maze','dodge','collect'):
            value=spec(kind);before=copy.deepcopy(value)
            checked=validate(value);self.assertEqual(checked,before)
            checked['start'][0]=2;self.assertEqual(value,before)

    def test_unknown_fields_types_ids_and_coordinates_are_rejected(self):
        bad=[dict(extra=True),dict(width=True),dict(seed=-1),dict(kind='platformer'),
             dict(id='../counter'),dict(start=[-1,0]),dict(walls=[[0,0]]),dict(title='bad\nname'),
             dict(walls=[[1,0],[1,0]]),dict(step_ms=0),dict(duration_ms=1)]
        for change in bad:
            with self.subTest(change=change),self.assertRaises(ValueError):validate(dict(spec(),**change))

    def test_unreachable_maze_and_collectible_are_rejected(self):
        for kind in ('maze','collect'):
            value=spec(kind);value['walls']=[[1,0],[0,1]]
            with self.assertRaises(ValueError):validate(value)
        value=spec('dodge');value['duration_ms']=1000
        with self.assertRaises(ValueError):validate(value)
