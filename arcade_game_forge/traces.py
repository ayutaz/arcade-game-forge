"""Independent evaluation sequences; never included in generator prompts."""
import random
from .reference import Game
from .spec import validate


def _path(spec,start,goal):
    queue=[start];previous={start:None};walls={tuple(p) for p in spec['walls']}
    for x,y in queue:
        if (x,y)==goal:break
        for key,(nx,ny) in ((1,(x+1,y)),(2,(x-1,y)),(4,(x,y+1)),(8,(x,y-1))):
            point=(nx,ny)
            if (0<=nx<spec['width'] and 0<=ny<spec['height'] and point not in walls and point not in previous):
                previous[point]=((x,y),key);queue.append(point)
    keys=[];point=goal
    while point!=start:
        parent,key=previous[point];keys.append(key);point=parent
    return list(reversed(keys))


def traces(spec,*,seed):
    spec=validate(spec);game=Game(spec);victory=[]
    def add(key,dt):
        victory.append((key,dt));game.step(key,dt)
    add(0,0);add(16,0);add(0,0)
    if spec['kind']=='dodge':
        for _ in range((spec['height']+1)*spec['target']+8):
            if game.phase!=1:break
            key=0
            if game.hazard is not None and game.hazard[0]==game.x:key=2 if game.x else 1
            add(0,0);add(key,spec['step_ms'])
    else:
        destinations=[tuple(spec['goal'])] if spec['kind']=='maze' else sorted(tuple(p) for p in spec['coins'])
        for destination in destinations:
            if game.phase!=1:break
            for key in _path(spec,(game.x,game.y),destination):add(0,0);add(key,0)
    if game.phase!=2:raise ValueError('reference victory failed; do not evaluate generated games')
    add(0,0);add(64,0)
    rng=random.Random(seed)
    random_frames=[(0,0),(16,0),(0,0)]
    for _ in range(128):
        random_frames.append((rng.choice((0,1,2,4,8,16,32,3,5,128,144,160,17)),
                              rng.choice((0,1,16,33,spec['step_ms'],1000,60000))))
    random_frames.extend(((0,0),(192,0)))
    return dict(victory=victory,random=random_frames,
                edges=[(0,0),(16,0),(0,0),(1,0),(1,0),(3,0),(0,10),(32,60000),(16,0),(0,60000),(192,0)],
                deadline=[(0,0),(16,0),(0,60000),(0,60000),(0,60000),(64,0)],
                back_priority=[(0,0),(16,0),(0,0),(97,60000)])
