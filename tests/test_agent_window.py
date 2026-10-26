import os
os.environ.setdefault('QT_QPA_PLATFORM','offscreen')
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
try:
    from PyQt6.QtWidgets import QApplication
except ImportError:QApplication=None

@unittest.skipIf(QApplication is None,'Qt indisponível')
class AgentWindowTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.app=QApplication.instance() or QApplication([])
    def test_configuration_does_not_launch_inference_and_can_recover_history(self):
        from ui_components.agent_workspace import AgentWindow
        with tempfile.TemporaryDirectory() as tmp,patch('ui_components.agent_workspace.project_root',return_value=Path(tmp)):
            panel=AgentWindow();panel.set_brief('Criar jogo')
            self.assertIsNone(panel.thread);self.assertEqual(len(panel.tasks),3)
            panel.store.save({'id':'x','created':0.,'state':'running','brief':'Projeto anterior','folder':tmp,'tasks':{'codigo':{'id':'codigo','role':'Código','prompt':'Teste','files':['a.txt'],'depends':[],'model':'sonnet','state':'running','started':1.,'characters':0}}})
            panel.refresh_history();panel.load_history(1)
            self.assertEqual(panel.tree.topLevelItem(0).text(1),'Sessão interrompida')
            self.assertIsNone(panel.thread);self.assertEqual(panel.brief.toPlainText(),'Projeto anterior')
            panel.hide();panel.deleteLater();self.app.processEvents()
    def test_voice_action_only_prepares_workspace(self):
        from actions.agent_workspace import agent_workspace
        from types import SimpleNamespace
        calls=[];player=SimpleNamespace(show_agent_workspace=calls.append)
        import json
        result=json.loads(agent_workspace({'brief':'Jogo'},player))
        self.assertEqual(result['status'],'prepared');self.assertEqual(calls,['Jogo'])
