import unittest
from core.startup_settings import startup_ready


class StartupSettingsTests(unittest.TestCase):
    def test_claude_can_start_without_gemini_for_typed_commands(self):
        self.assertTrue(startup_ready({'brain_provider': 'claude_code'}))

    def test_gemini_requires_key_and_operating_system(self):
        self.assertFalse(startup_ready({'brain_provider': 'gemini'}))
        self.assertFalse(startup_ready({'brain_provider': 'gemini', 'gemini_api_key': 'test'}))
        self.assertTrue(startup_ready({'brain_provider': 'gemini', 'gemini_api_key': 'test', 'os_system': 'Windows'}))

    def test_new_install_still_opens_setup(self):
        self.assertFalse(startup_ready({}))
