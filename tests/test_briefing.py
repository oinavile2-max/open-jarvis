import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import unittest
from core.search_cards import search_cards

class BriefingDataTests(unittest.TestCase):
    def test_news_format_exposes_source_and_image(self):
        from actions.web_search import _format_news
        text=_format_news('ciência',[{'title':'Descoberta','snippet':'Resumo real','url':'https://example.com/news','image':'https://example.com/photo.jpg','source':'Jornal'}])
        cards=search_cards(text)
        self.assertEqual(len(cards),1)
        self.assertEqual(cards[0]['image'],'https://example.com/photo.jpg')
        self.assertEqual(cards[0]['summary'],'Resumo real')

    def test_legacy_news_and_unsafe_image(self):
        cards=search_cards('1. Manchete\nResumo\nhttps://example.com/a\nImage: file:///private.png')
        self.assertEqual(len(cards),1)
        self.assertIsNone(cards[0]['image'])
        self.assertEqual(cards[0]['summary'],'Resumo')

try:
    from PyQt6.QtWidgets import QApplication
except ImportError:
    QApplication=None

@unittest.skipIf(QApplication is None,'PyQt6 indisponível')
class BriefingUiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app=QApplication.instance() or QApplication([])

    def test_selection_updates_detail_without_network_or_timer_rotation(self):
        from ui_components.briefing import BriefingDeck
        deck=BriefingDeck()
        deck.set_content('Pesquisa','1. Primeira\nResumo um\nSource: https://example.com/1\n\n2. Segunda\nResumo dois\nSource: https://example.com/2')
        deck.select(1)
        self.assertEqual(deck.title.text(),'Segunda')
        self.assertEqual(deck.summary.toPlainText(),'Resumo dois')
        self.assertEqual(deck.selected_url,'https://example.com/2')
        deck.close()

    def test_empty_content_clears_old_source_and_profile_is_not_authentication(self):
        from types import SimpleNamespace
        from ui_components.briefing import BriefingDeck,BriefingWindow
        from PyQt6.QtGui import QPixmap
        deck=BriefingDeck();deck.set_content('Pesquisa','1. Um\nTexto\nSource: https://example.com')
        deck.set_content('Resposta','Sem fontes nesta resposta')
        self.assertIsNone(deck.selected_url);self.assertFalse(deck.source.isEnabled())
        hud=SimpleNamespace(state='LISTENING',speaking=False,_amp_disp=0.,_profile_data={'name':'Ana'},_profile_pixmap=QPixmap(),_profile_opacity=1.,_profile_verified_until=0.,caption='')
        panel=BriefingWindow(hud);panel.sync()
        self.assertNotIn('verificada',panel.identity.text().lower())
        hud.state='SLEEPING';panel.sync();self.assertTrue(panel.identity.isHidden())
        panel.close();deck.close()

    def test_article_image_load_is_async_and_old_selection_cannot_overwrite(self):
        import threading,time
        from unittest.mock import patch
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        from PyQt6.QtCore import QBuffer,QIODevice
        from PyQt6.QtGui import QImage,QColor
        from PyQt6.QtTest import QTest
        from ui_components.briefing import BriefingDeck
        image=QImage(8,8,QImage.Format.Format_RGB32);image.fill(QColor('#22aa44'))
        buffer=QBuffer();buffer.open(QIODevice.OpenModeFlag.WriteOnly);image.save(buffer,'PNG');png=bytes(buffer.data())
        seen=threading.Event()
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                seen.set()
                if self.path=='/slow':time.sleep(.15)
                self.send_response(200);self.send_header('Content-Type','image/png');self.end_headers()
                try:self.wfile.write(png)
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
        resolver=patch('ui_components.briefing.resolve_public_image',side_effect=lambda url,callback:callback(True));resolver.start()
        deck=BriefingDeck();base=f'http://127.0.0.1:{server.server_port}'
        try:
            deck.set_content('Teste',f'1. Antigo\nTexto\nSource: https://example.com/1\nImage: {base}/slow\n\n2. Atual\nNovo\nSource: https://example.com/2\nImage: {base}/fast')
            self.assertFalse(seen.is_set(),'Painel oculto não deve buscar imagem')
            deck.show();QTest.qWait(30);deck.select(1)
            deadline=time.monotonic()+3
            while deck.image.pixmap() is None and time.monotonic()<deadline:QTest.qWait(10)
            QTest.qWait(200)
            self.assertEqual(deck.title.text(),'Atual')
            self.assertFalse(deck.image.pixmap().isNull())
            self.assertNotIn(base+'/slow',deck._cache)
            deck.hide();self.assertIsNone(deck._reply)
        finally:
            deck.close();server.shutdown();server.server_close();resolver.stop()

    def test_private_image_is_rejected_before_http(self):
        from ui_components.briefing import BriefingDeck
        deck=BriefingDeck()
        deck.set_content('Teste','1. Um\nTexto\nSource: https://example.com\nImage: http://127.0.0.1/private')
        deck.show();self.app.processEvents()
        self.assertIsNone(deck._reply)
        self.assertIn('http://127.0.0.1/private',deck._failed)
        deck.close()

    def test_total_deadline_stops_a_trickle_response(self):
        import threading,time
        from unittest.mock import patch
        from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
        from PyQt6.QtTest import QTest
        from ui_components.briefing import BriefingDeck
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args):pass
            def do_GET(self):
                self.send_response(200);self.end_headers()
                try:
                    for _ in range(20):
                        self.wfile.write(b'x');self.wfile.flush();time.sleep(.03)
                except (BrokenPipeError,ConnectionResetError):pass
        server=ThreadingHTTPServer(('127.0.0.1',0),Handler)
        threading.Thread(target=server.serve_forever,daemon=True).start()
        with patch('ui_components.briefing.resolve_public_image',side_effect=lambda url,callback:callback(True)):
            deck=BriefingDeck();url=f'http://127.0.0.1:{server.server_port}/trickle'
            try:
                deck.set_content('Teste',f'1. Um\nTexto\nSource: https://example.com\nImage: {url}')
                deck.show();deck.deadline.start(120)
                QTest.qWait(250)
                self.assertIsNone(deck._reply)
                self.assertIn(url,deck._failed)
            finally:deck.close();server.shutdown();server.server_close()
