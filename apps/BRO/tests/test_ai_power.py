import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
import unittest
from unittest.mock import patch
import ai_power
class AIPowerTests(unittest.TestCase):
    def test_service_shutdown_verified(self):
        with patch.object(ai_power,'reachable',side_effect=[True,False]),patch.object(ai_power,'service') as service:
            self.assertIn('endpoint offline',ai_power.stop());service.assert_called_once_with('stop')
    def test_failure_unloads_without_claiming_shutdown(self):
        with patch.object(ai_power,'reachable',return_value=True),patch.object(ai_power,'service',return_value=False),patch.object(ai_power,'api',side_effect=[{'models':[{'name':'test'}]},{}]) as api:
            self.assertIn('service still running',ai_power.stop())
            self.assertEqual(api.call_args[0],('/api/generate',{'model':'test','keep_alive':0}))
    def test_already_stopped(self):
        with patch.object(ai_power,'reachable',return_value=False),patch.object(ai_power,'service') as service:
            self.assertIn('already stopped',ai_power.stop());service.assert_not_called()
