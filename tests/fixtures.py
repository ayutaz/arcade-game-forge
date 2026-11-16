def spec(kind='maze'):
    result=dict(schema=1,kind=kind,id='forge-'+kind,title='Forge '+kind.title(),version='1.0.0',
                width=6,height=6,start=[0,0],walls=[[1,0]],goal=[2,0],coins=[],target=1,
                step_ms=500,duration_ms=60000,seed=1)
    if kind=='collect':result.update(goal=None,coins=[[0,1],[1,1]],target=2)
    if kind=='dodge':result.update(width=3,start=[1,5],walls=[],goal=None,coins=[],target=1)
    return result
