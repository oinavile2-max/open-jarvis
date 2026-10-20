import unittest
from core.search_cards import safe_url,search_cards
class TestSearchCards(unittest.TestCase):
 def test_parser_separates_results(self):
  cards=search_cards('Search results for: q\n\n1. Título\n   Resumo.\n   Source: https://example.com/a\n\n2. Outro\n   Texto\n   Source: https://example.org')
  self.assertEqual(len(cards),2);self.assertEqual(cards[0]['domain'],'example.com');self.assertEqual(cards[0]['summary'],'Resumo.')
 def test_rejects_executable_and_credential_urls(self):
  for url in ['javascript:alert(1)','file:///etc/passwd','https://user:pass@example.com']:
   self.assertIsNone(safe_url(url))
