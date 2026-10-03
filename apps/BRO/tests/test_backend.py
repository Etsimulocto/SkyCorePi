import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from unittest.mock import patch
from backend import Backend,SPEAKERS

class BackendTests(unittest.TestCase):
    def test_original_cards_and_separate_history(self):
        b=Backend()
        for speaker in SPEAKERS:
            self.assertIn(speaker,b.prompt(speaker))
        b.commit('Sky','hello','reply')
        self.assertEqual(len(b.prepare('Sky','next')[0]),4)
        self.assertEqual(len(b.prepare('Cold','next')[0]),2)
        self.assertIn('archetype_sky_001',b.prompt('Sky'))
    def test_bounded_history(self):
        b=Backend()
        for _ in range(20):b.commit('BRO','input','reply')
        self.assertEqual(len(b.histories['BRO']),20)
    def test_local_request_attribution(self):
        b=Backend();messages,_=b.prepare('GRIT','build')
        with patch.object(b,'request',return_value={'message':{'content':'Ready.'}}) as request:
            self.assertEqual(b.ask('test',messages),'Ready.')
            self.assertEqual(request.call_args[0][0],'/api/chat')
        self.assertEqual(b.histories['GRIT'],[])
    def test_unknown_identity_rejected(self):
        with self.assertRaises(ValueError):Backend().prompt('Other')
