"""Focused evaluator-boundary tests; fixtures prove mechanics, not scientific authenticity."""
from __future__ import annotations
import unittest
from unittest.mock import MagicMock, patch

import evaluate_s11_closed_loop as s11

class S11IntegrityTests(unittest.TestCase):
    def test_missing_consumed_input_is_rejected(self):
        run = MagicMock(); run.name = "fixture"
        with patch.object(s11, "manifest_entries", return_value={"capture_seg1.pcap": "0" * 64}):
            with self.assertRaisesRegex(RuntimeError, "lacks evaluator input"):
                s11.verify_run_inputs(run)

    def test_duplicate_basename_is_rejected(self):
        manifest = MagicMock()
        manifest.read_text.return_value = f"{'0' * 64}  one/capture_seg1.pcap\n{'1' * 64}  two/capture_seg1.pcap\n"
        with self.assertRaisesRegex(RuntimeError, "duplicate manifest basename"):
            s11.manifest_entries(manifest)

    def test_malformed_line_is_rejected(self):
        manifest = MagicMock()
        manifest.read_text.return_value = "not a manifest\n"
        with self.assertRaisesRegex(RuntimeError, "malformed manifest line"):
            s11.manifest_entries(manifest)

    def test_master_transition_is_ineligible(self):
        self.assertFalse(s11.receiver_state_eligible([(1.0, 1, "UNCALIBRATED to MASTER on X")]))
        self.assertTrue(s11.receiver_state_eligible([(1.0, 2, "LISTENING to UNCALIBRATED on X")]))


if __name__ == "__main__":
    unittest.main()
