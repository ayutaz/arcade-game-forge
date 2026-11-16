"""Behavioral oracle, independent of generated C, graphics and compilers."""
from .spec import validate


class Game:
    def __init__(self,spec):
        self.spec=validate(spec);self.previous=0;self.reset()

    def reset(self):
        self.phase=0;self.score=0;self.elapsed=0;self.accumulator=0
        self.x,self.y=self.spec['start'];self.random=self.spec['seed']
        self.coins={tuple(point) for point in self.spec['coins']};self.hazard=None

    def snapshot(self):
        return dict(value=(self.phase<<16)|self.score,x=self.x,y=self.y,elapsed=self.elapsed)

    def step(self,held,dt):
        if type(held) is not int or not 0<=held<=255 or type(dt) is not int or not 0<=dt<=60000:
            raise ValueError('input/time bounds')
        pressed=held&~self.previous
        if pressed&64:return True
        self.previous=held
        if pressed&32:self.reset();return False
        if self.phase==0:
            if pressed&16:self.phase=1
            return False
        if self.phase!=1:return False
        self.elapsed=min(self.spec['duration_ms'],self.elapsed+dt)
        if self.elapsed==self.spec['duration_ms']:self.phase=3;return False
        dx,dy=(1,0) if pressed&1 else (-1,0) if pressed&2 else (0,1) if pressed&4 else (0,-1) if pressed&8 else (0,0)
        if self.spec['kind']=='dodge':dy=0
        nx,ny=self.x+dx,self.y+dy
        if (0<=nx<self.spec['width'] and 0<=ny<self.spec['height'] and [nx,ny] not in self.spec['walls']):
            self.x,self.y=nx,ny
        if self.spec['kind']=='maze' and [self.x,self.y]==self.spec['goal']:
            self.score=1;self.phase=2
        elif self.spec['kind']=='collect':
            if (self.x,self.y) in self.coins:self.coins.remove((self.x,self.y));self.score+=1
            if not self.coins:self.phase=2
        elif self.spec['kind']=='dodge':
            self.accumulator+=dt
            while self.accumulator>=self.spec['step_ms'] and self.phase==1:
                self.accumulator-=self.spec['step_ms']
                if self.hazard is not None:
                    hx,hy=self.hazard;self.hazard=(hx,hy+1)
                    if hy+1>=self.spec['height']:
                        self.score+=1;self.hazard=None
                        if self.score==self.spec['target']:self.phase=2;break
                if self.hazard is None:
                    self.random=(1664525*self.random+1013904223)&0xffffffff
                    self.hazard=(self.random%self.spec['width'],0)
                if self.hazard==(self.x,self.y):self.phase=3
        return False
