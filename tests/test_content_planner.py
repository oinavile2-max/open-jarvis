"""Public planning interface: persistence, calendar and rollback."""
import tempfile
from pathlib import Path
import unittest
from core.content_planner import ContentPlanner, plan_markdown


class ContentPlannerTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'plans.sqlite3'
        self.planner = ContentPlanner(self.path)
    def tearDown(self): self.tmp.cleanup()

    def test_week_dates_scripts_and_status_survive_restart(self):
        key = self.planner.create_plan('Minha semana', '2026-10-26', 'Tecnologia', [
            {'day': 0, 'title': 'Uma ideia', 'script': 'Roteiro completo', 'hook': 'Gancho', 'cta': 'Comente'},
            {'day': 6, 'title': 'Domingo', 'channel': 'YouTube'}])
        plan = ContentPlanner(self.path).get_plan(key)
        self.assertEqual([c['scheduled_date'] for c in plan['cards']], ['2026-10-26', '2026-11-01'])
        self.planner.update_card(plan['cards'][0]['id'], {'status': 'gravado'})
        self.assertEqual(self.planner.get_plan(key)['cards'][0]['status'], 'gravado')
        output = plan_markdown(self.planner.get_plan(key))
        self.assertIn('Roteiro completo', output)
        self.assertIn('## Domingo', output)

    def test_invalid_day_leaves_no_partial_plan(self):
        with self.assertRaises(ValueError):
            self.planner.create_plan('Inválido', '2026-10-26', '', [{'day': 0, 'title': 'OK'}, {'day': 7, 'title': 'Não'}])
        self.assertEqual(self.planner.list_plans(), [])

    def test_card_revision_detects_concurrent_edits(self):
        key = self.planner.create_plan('Plano', '2026-10-26', '', [{'day': 0, 'title': 'Original'}])
        card = self.planner.get_plan(key)['cards'][0]
        self.planner.update_card(card['id'], {'title': 'Novo'}, expected_revision=card['revision'])
        with self.assertRaises(ValueError):
            self.planner.update_card(card['id'], {'title': 'Obsoleto'}, expected_revision=card['revision'])
        self.assertEqual(self.planner.get_plan(key)['cards'][0]['title'], 'Novo')

    def test_date_must_be_monday_and_publish_needs_plan(self):
        with self.assertRaises(ValueError): self.planner.create_plan('Plano', '2026-10-27', '', [])
        with self.assertRaises(ValueError): self.planner.get_plan('missing')
