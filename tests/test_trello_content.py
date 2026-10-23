import tempfile
from pathlib import Path
import unittest
from core.content_planner import ContentPlanner
from core.trello_content import TrelloError, publish_plan, TrelloClient


class TrelloMemoryTransport:
    """Protocol test server state; never used by product code."""
    def __init__(self): self.cards=[];self.lists=[];self.boards=[];self.timeout_after_create=False
    def request(self,method,url,headers,params,timeout):
        assert 'key=' not in url and 'token=' not in url
        path=url.removeprefix('https://api.trello.com/1')
        if method=='GET' and path=='/members/me/boards': value=self.boards.copy()
        elif method=='POST' and path=='/boards':
            value={'id':'board12345','desc':params['desc']};self.boards.append(value)
        elif method=='GET' and path.endswith('/lists'): value=self.lists.copy()
        elif method=='GET' and path.endswith('/cards'): value=self.cards.copy()
        elif method=='POST' and path=='/lists':
            value={'id':'list'+str(len(self.lists)),**params};self.lists.append(value)
        elif method=='POST' and path=='/cards':
            value={'id':'card'+str(len(self.cards)),**params};self.cards.append(value)
            if self.timeout_after_create:
                self.timeout_after_create=False
                raise TimeoutError('request lost after commit')
        else: raise AssertionError((method,path))
        class Response:
            status_code=200
            def json(self): return value
        return Response()


class TrelloPublishTests(unittest.TestCase):
    def setUp(self):
        self.tmp=tempfile.TemporaryDirectory(); self.planner=ContentPlanner(Path(self.tmp.name)/'test.sqlite3')
        self.key=self.planner.create_plan('Semana de teste','2026-10-26','',[{'day':0,'title':'Primeiro','script':'Texto de teste'}])
        self.transport=TrelloMemoryTransport()
        self.client=TrelloClient({'trello_api_key':'key','trello_token':'token'},transport=self.transport)
    def tearDown(self): self.tmp.cleanup()
    def test_publish_reconciles_previous_cards_and_preserves_remote_edits(self):
        first=publish_plan(self.planner,self.key,{},confirmed=True,client=self.client)
        self.assertEqual(first['created'],1)
        self.transport.cards[0]['name']='Edição feita no Trello'
        self.transport.cards[0]['desc']='Roteiro editado remotamente sem marcador JARVIS'
        self.transport.boards[0]['desc']='Quadro editado sem marcador'
        second=publish_plan(self.planner,self.key,{},confirmed=True,client=self.client)
        self.assertEqual(second['existing'],1)
        self.assertEqual(len(self.transport.boards),1)
        self.assertEqual(len(self.transport.cards),1)
        self.assertEqual(len(self.transport.lists),7)
        self.assertEqual(self.transport.cards[0]['name'],'Edição feita no Trello')
    def test_timeout_after_remote_creation_does_not_duplicate_on_retry(self):
        self.transport.timeout_after_create=True
        with self.assertRaises(TrelloError): publish_plan(self.planner,self.key,{},confirmed=True,client=self.client)
        result=publish_plan(self.planner,self.key,{},confirmed=True,client=self.client)
        self.assertEqual(result['created'],0)
        self.assertEqual(result['existing'],1)
        self.assertEqual(len(self.transport.cards),1)
    def test_publish_requires_explicit_confirmation(self):
        with self.assertRaises(TrelloError): publish_plan(self.planner,self.key,{},client=self.client)
        self.assertEqual(self.transport.boards,[])
    def test_concurrent_publish_is_rejected(self):
        with self.planner.publish_lock(self.key):
            with self.assertRaises(ValueError): publish_plan(self.planner,self.key,{},confirmed=True,client=self.client)
    def test_cancel_after_request_stops_further_remote_writes(self):
        import threading
        stop=threading.Event()
        original=self.transport.request
        def request(method,url,**kwargs):
            result=original(method,url,**kwargs)
            if method=='POST' and url.endswith('/lists'):stop.set()
            return result
        self.transport.request=request
        with self.assertRaises(TrelloError):
            publish_plan(self.planner,self.key,{},confirmed=True,client=self.client,stop=stop)
        self.assertEqual(len(self.transport.lists),1)
        self.assertEqual(self.transport.cards,[])

    def test_transport_errors_never_expose_tokens(self):
        class Broken:
            def request(self,*args,**kwargs): raise RuntimeError('secret-token from upstream')
        client=TrelloClient({'trello_api_key':'key','trello_token':'secret-token'},transport=Broken())
        with self.assertRaises(TrelloError) as error: client.check_connection()
        self.assertNotIn('secret-token',str(error.exception))
