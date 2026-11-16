import hashlib
import unittest
from arcade_game_forge.deploy import install_game

PACKAGE=b'fixture package';HASH=hashlib.sha256(PACKAGE).hexdigest()

class Client:
    def __init__(self):
        self.rows=[dict(id='existing',title='Existing',version='1.0.0',sha256='a'*64)]
        self.status=dict(mode=0,held=0,remaining_ms=0,active_id='');self.writes=0
    def control_status(self):return dict(self.status)
    def list_apps(self):return [dict(row) for row in self.rows]
    def install(self,package):
        self.writes+=1;self.rows=[row for row in self.rows if row['id']!='forge-maze']
        self.rows.append(dict(id='forge-maze',title='Forge Maze',version='1.0.0',sha256=HASH))

class DeployTests(unittest.TestCase):
    def decode(self,package):return dict(id='forge-maze',title='Forge Maze',version='1.0.0',capabilities=['draw']),b''
    def test_owned_app_addition_and_exact_previous_hash_update(self):
        client=Client();before=client.list_apps()
        result=install_game(client,PACKAGE,self.decode)
        self.assertEqual(result['sha256'],HASH);self.assertEqual(client.rows[0],before[0])
        with self.assertRaises(ValueError):install_game(client,PACKAGE,self.decode)
        install_game(client,PACKAGE,self.decode,previous_sha=HASH);self.assertEqual(client.writes,2)

    def test_foreign_id_capability_active_state_full_or_changed_catalog_fail_closed(self):
        for mode in ('id','cap','active','held','full','corrupt'):
            client=Client();manifest,_=self.decode(PACKAGE)
            if mode=='id':manifest['id']='counter'
            if mode=='cap':manifest['capabilities']=['draw','storage']
            if mode=='active':client.status.update(mode=1,active_id='existing')
            if mode=='held':client.status['held']=1
            if mode=='full':client.rows=[dict(client.rows[0],id='existing-'+str(i)) for i in range(16)]
            if mode=='corrupt':
                original=client.install
                def corrupt(package):original(package);client.rows[0]['sha256']='b'*64
                client.install=corrupt
            with self.assertRaises((ValueError,RuntimeError)):install_game(client,PACKAGE,lambda _: (manifest,b''))
            self.assertEqual(client.writes,1 if mode=='corrupt' else 0)
