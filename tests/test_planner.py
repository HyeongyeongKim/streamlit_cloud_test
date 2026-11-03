import unittest
from datetime import time
from planner import schedule_values, timing, clean_theme, BASE, PALETTES, contrast, ink_on


class PlannerTests(unittest.TestCase):
    def test_optional_time_and_boundary_grouping(self):
        self.assertEqual(schedule_values('anytime', None, None)['timeBand'], 'anytime')
        self.assertEqual(schedule_values('night', None, None)['timeBand'], 'night')
        for start, expected in [(time(0), 'morning'), (time(11,59), 'morning'), (time(12), 'afternoon'), (time(18), 'night')]:
            self.assertEqual(schedule_values('anytime', start, None)['timeBand'], expected)

    def test_invalid_ranges_and_fixed_appointments(self):
        for args in [('morning', None, time(10)), ('night', time(23), time(1)), ('morning', None, None, True), ('morning', time(9), time(9))]:
            with self.assertRaises(ValueError):
                schedule_values(*args)
        with self.assertRaises(ValueError):
            schedule_values('anytime', None, None, False, time(14), time(13))

    def test_shared_time_hidden_and_legacy_default(self):
        task = {'time_band':'afternoon', 'planned_start':'14:00', 'planned_end':'15:00', 'share_time':0}
        self.assertEqual(timing(task, shared=True), '시간 비공개')
        self.assertEqual(timing({}), '오늘 중')

    def test_invalid_theme_sanitized_and_palettes_readable(self):
        for bad in ([], None, {'text':'red; color:white', 'font':'unknown'}):
            self.assertEqual(clean_theme(bad), BASE)
        for theme in PALETTES.values():
            self.assertGreaterEqual(contrast(theme['text'], theme['card']), 4.5)
            self.assertGreaterEqual(contrast(ink_on(theme['accent']), theme['accent']), 4.5)
