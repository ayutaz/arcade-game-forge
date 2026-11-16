"""Validate a small, closed game specification before generation or execution."""
import copy
import re

FIELDS={'schema','kind','id','title','version','width','height','start','walls','goal','coins',
        'target','step_ms','duration_ms','seed'}


def validate(value):
    if type(value) is not dict or set(value)!=FIELDS:raise ValueError('game spec schema')
    for key,lo,hi in (('schema',1,1),('width',3,12),('height',4,10),('target',1,10),
                      ('step_ms',100,1500),('duration_ms',1000,180000),('seed',0,0xffffffff)):
        if type(value[key]) is not int or not lo<=value[key]<=hi:raise ValueError(key+' bounds')
    kind=value['kind']
    if kind not in ('maze','dodge','collect') or value['id']!='forge-'+kind:raise ValueError('owned kind/id')
    if (type(value['title']) is not str or not re.fullmatch(r'[A-Za-z0-9 -]{1,20}',value['title']) or
        type(value['version']) is not str or not re.fullmatch(r'[0-9]{1,4}\.[0-9]{1,4}\.[0-9]{1,4}',value['version'])):
        raise ValueError('title/version')
    def point(position):
        if (type(position) is not list or len(position)!=2 or any(type(v) is not int for v in position) or
            not 0<=position[0]<value['width'] or not 0<=position[1]<value['height']):
            raise ValueError('board coordinate')
        return tuple(position)
    start=point(value['start'])
    def points(key,maximum):
        entries=value[key]
        if type(entries) is not list or len(entries)>maximum:raise ValueError(key+' quota')
        result={point(p) for p in entries}
        if len(result)!=len(entries):raise ValueError('duplicate '+key)
        return result
    walls=points('walls',40);coins=points('coins',8)
    if start in walls or start in coins or walls&coins:raise ValueError('overlapping board entities')
    if kind=='dodge':
        if (walls or coins or value['goal'] is not None or value['width']>8 or start[1]!=value['height']-1 or
            value['duration_ms']<value['step_ms']*(1+value['height']*value['target'])):
            raise ValueError('dodge board/deadline')
    else:
        if kind=='maze':
            goal=point(value['goal'])
            if coins or goal in walls or goal==start or value['target']!=1:raise ValueError('maze goal')
            destinations={goal}
        else:
            if value['goal'] is not None or not coins or value['target']!=len(coins):raise ValueError('collect targets')
            destinations=coins
        reachable={start};queue=[start]
        for x,y in queue:
            for next_point in ((x+1,y),(x-1,y),(x,y+1),(x,y-1)):
                nx,ny=next_point
                if (0<=nx<value['width'] and 0<=ny<value['height'] and next_point not in walls and next_point not in reachable):
                    reachable.add(next_point);queue.append(next_point)
        if not destinations<=reachable:raise ValueError('unreachable objective')
    return copy.deepcopy(value)
