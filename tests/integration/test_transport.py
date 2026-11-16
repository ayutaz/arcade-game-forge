import os
from pathlib import Path
import unittest
SDK=Path(os.environ.get('ARCADE_OS_ROOT',str(Path(__file__).resolve().parents[3]/'scratch-arcade-os')))

class DelayedBootTransportTests(unittest.TestCase):
    def test_connect_waits_for_a_slow_initial_beacon_without_sending_or_resetting_early(self):
        import importlib,struct
        from contextlib import contextmanager
        from unittest.mock import patch
        from arcade_game_forge.sdk import load_sdk
        from arcade_game_forge.deploy import transport
        load_sdk(SDK)
        module=importlib.import_module('labos.transfer');clock=[0.0];writes=[]
        class Stream:
            def __init__(self):self.pending=b''
            def read(self,n):
                clock[0]+=.1
                if self.pending:result=self.pending;self.pending=b'';return result
                if clock[0]>=3.5:
                    return module.encode(module.Frame(1,0,0,module.SIGNATURE+struct.pack('<4I',17,16384,512,2),response=True))
                return b''
            def write(self,data):
                self.assert_ready=clock[0]>=3.5
                writes.append((clock[0],data));frame=module.Parser().feed(data)[0]
                self.pending=module.encode(module.Frame(frame.op,frame.session,frame.request,b'',response=True))
                return len(data)
        @contextmanager
        def connection(port):yield Stream()
        original=module.Client
        def factory(stream,**kwargs):return original(stream,clock=lambda:clock[0],**kwargs)
        with patch.object(module,'serial_connection',connection),patch.object(module,'Client',factory):
            _,connect=transport(SDK)
            with connect('fake-port') as client:self.assertTrue(client.connected)
        self.assertTrue(writes);self.assertTrue(all(when>=3.5 for when,_ in writes))
        self.assertLess(clock[0],12)
