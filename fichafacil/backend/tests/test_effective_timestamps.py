from datetime import datetime, timezone
from types import SimpleNamespace
import unittest

from app.utils.corrections import get_effective_timestamp


class EffectiveTimestampTests(unittest.TestCase):
    def test_returns_original_timestamp_without_approved_correction(self):
        original = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
        fichaje = SimpleNamespace(id=1, timestamp=original)

        self.assertEqual(get_effective_timestamp(fichaje, {}), original)

    def test_returns_corrected_timestamp_when_approved_correction_exists(self):
        original = datetime(2026, 1, 1, 8, 0, tzinfo=timezone.utc)
        corrected = datetime(2026, 1, 1, 8, 15, tzinfo=timezone.utc)
        fichaje = SimpleNamespace(id=1, timestamp=original)

        self.assertEqual(get_effective_timestamp(fichaje, {1: corrected}), corrected)


if __name__ == "__main__":
    unittest.main()
