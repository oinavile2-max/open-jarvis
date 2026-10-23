"""Native UI verification against persisted data, without provider accounts."""
import importlib.util
import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
import time
import unittest
from pathlib import Path
from core.content_planner import ContentPlanner,DAYS


@unittest.skipUnless(importlib.util.find_spec('PyQt6'),'PyQt6 not installed')
class ContentWorkspaceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        from PyQt6.QtWidgets import QApplication
        cls.app=QApplication.instance() or QApplication([])
    def test_command_entry_keeps_gui_responsive_with_slow_provider(self):
        from PyQt6.QtCore import Qt,QTimer
        from PyQt6.QtTest import QTest
        from ui_components.content_workspace import ContentWorkspace
        import threading
        release=threading.Event();done=threading.Event()
        def slow(text):
            release.wait(2);done.set()
        with tempfile.TemporaryDirectory() as folder:
            panel=ContentWorkspace(planner=ContentPlanner(Path(folder)/'content.sqlite3'),send_command=slow)
            panel.show();self.app.processEvents()
            try:
                panel.command.setText('Um comando')
                QTimer.singleShot(10,release.set)
                started=time.monotonic();QTest.keyClick(panel.command,Qt.Key.Key_Return)
                self.app.processEvents()
                self.assertLess(time.monotonic()-started,1)
            finally:
                release.set();done.wait(2);panel.shutdown();panel.close();self.app.processEvents()

    def test_saved_plan_selection_loads_new_cards(self):
        from PyQt6.QtWidgets import QLabel
        from ui_components.content_workspace import ContentWorkspace
        with tempfile.TemporaryDirectory() as folder:
            planner=ContentPlanner(Path(folder)/'plans.sqlite3')
            planner.create_plan('Antigo','2026-10-26','',[{'day':0,'title':'Cartão antigo'}])
            panel=ContentWorkspace(planner=planner);panel.show()
            try:
                self.app.processEvents()
                new=planner.create_plan('Novo','2026-10-26','',[{'day':1,'title':'Cartão recém-gerado'}])
                panel.select_plan(new)
                end=time.monotonic()+5
                while time.monotonic()<end:
                    self.app.processEvents()
                    texts=[w.text() for w in panel.findChildren(QLabel)]
                    if 'Cartão recém-gerado' in texts:break
                    time.sleep(.01)
                self.assertIn('Cartão recém-gerado',texts)
                self.assertEqual(panel.plans.currentData(),new)
            finally:panel.shutdown();panel.close();self.app.processEvents()

    def test_saved_week_and_script_are_visible_in_native_widgets(self):
        from PyQt6.QtWidgets import QLabel,QDialogButtonBox
        from ui_components.content_workspace import ContentWorkspace,CardEditor
        with tempfile.TemporaryDirectory() as folder:
            planner=ContentPlanner(Path(folder)/'plans.sqlite3')
            key=planner.create_plan('Semana real','2026-10-26','',[
                {'day':3,'title':'Roteiro persistido','script':'Texto salvo no banco local.'}])
            panel=ContentWorkspace(planner=planner);panel.show();panel.set_view(1)
            try:
                end=time.monotonic()+5
                while time.monotonic()<end:
                    self.app.processEvents()
                    texts=[w.text() for w in panel.findChildren(QLabel)]
                    if 'Roteiro persistido' in texts:break
                    time.sleep(.01)
                self.assertIn('Roteiro persistido',texts)
                for day in DAYS:self.assertIn(day.upper(),texts)
                editor=CardEditor(planner.get_plan(key)['cards'][0],panel)
                self.assertEqual(editor.script.toPlainText(),'Texto salvo no banco local.')
                controls=editor.findChild(QDialogButtonBox)
                self.assertEqual(controls.button(QDialogButtonBox.StandardButton.Save).text(),'Salvar')
                editor.close()
            finally:
                panel.shutdown();panel.close();self.app.processEvents()
