import unittest
from datetime import date, datetime
from time_lords_logic import TimeLordsLogic
from flatlib import const
import pandas as pd

class TestTimeLordsLogic(unittest.TestCase):
    def setUp(self):
        self.logic = TimeLordsLogic()

    def test_get_firdaria_data_day(self):
        # Day birth sequence: Sun (10), Venus (8), Mercury (13), Moon (9), Saturn (11), Jupiter (12), Mars (7), NN (3), SN (2)
        birth_date = "1990/01/01"
        is_day = True

        # Test active lord on birth date
        current_date = date(1990, 1, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)

        self.assertEqual(data['is_day'], True)
        self.assertEqual(data['active']['major'], const.SUN)
        self.assertEqual(data['active']['minor'], const.SUN)

        # Test active lord 11 years later (should be Venus)
        # 10 years * 365.25 = 3652.5 days.
        # 1990/01/01 + 3652.5 days is approx 2000/01/01
        current_date = date(2001, 1, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)
        self.assertEqual(data['active']['major'], const.VENUS)

    def test_get_firdaria_data_night(self):
        # Night birth sequence: Moon (9), Saturn (11), Jupiter (12), Mars (7), Sun (10), Venus (8), Mercury (13), NN (3), SN (2)
        birth_date = "1990/01/01"
        is_day = False

        # Test active lord on birth date
        current_date = date(1990, 1, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)

        self.assertEqual(data['is_day'], False)
        self.assertEqual(data['active']['major'], const.MOON)
        self.assertEqual(data['active']['minor'], const.MOON)

        # Test active lord 10 years later (should be Saturn, because Moon is 9 years)
        current_date = date(2000, 1, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)
        self.assertEqual(data['active']['major'], const.SATURN)

    def test_firdaria_node_periods(self):
        # Day birth sequence: 10+8+13+9+11+12+7 = 70 years.
        # NN starts after 70 years.
        birth_date = "1900/01/01"
        is_day = True

        # 71 years later should be NN
        current_date = date(1971, 1, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)
        self.assertEqual(data['active']['major'], const.NORTH_NODE)
        self.assertEqual(data['active']['minor'], const.NORTH_NODE)

    def test_firdaria_sub_periods(self):
        # Sun major period (10 years) has 7 sub-periods of 10/7 years each.
        # Order: Sun, Venus, Mercury, Moon, Saturn, Jupiter, Mars
        birth_date = "2000/01/01"
        is_day = True

        # First sub-period is Sun-Sun
        current_date = date(2000, 1, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)
        self.assertEqual(data['active']['major'], const.SUN)
        self.assertEqual(data['active']['minor'], const.SUN)

        # Sub-period duration = 10 * 365.25 / 7 = 521.78 days
        # Second sub-period (Sun-Venus) starts after 521.78 days.
        # 2000/01/01 + 522 days is 2001/06/06 (approx)
        current_date = date(2001, 7, 1)
        data = self.logic.get_firdaria_data(birth_date, is_day, current_date)
        self.assertEqual(data['active']['major'], const.SUN)
        self.assertEqual(data['active']['minor'], const.VENUS)

    def test_default_current_date(self):
        # Should not raise error and return something reasonable
        birth_date = "1980/01/01"
        data = self.logic.get_firdaria_data(birth_date, True)
        self.assertIn('active', data)
        self.assertIn('timeline', data)
        self.assertIsInstance(data['active']['start'], (date, datetime, pd.Timestamp))

    def test_date_edge_cases(self):
        birth_date = "2000/01/01"
        # Before birth date
        current_date = date(1999, 12, 31)
        data = self.logic.get_firdaria_data(birth_date, True, current_date)
        # Based on logic: if sub_start <= current_date < sub_end
        # 1999/12/31 is before birth_dt, so active might be None
        self.assertIsNone(data['active']['major'])

        # Exactly at major period boundary
        # Sun ends at birth + 10 * 365.25 days = 2010/01/01 (approx)
        # Actually 10 * 365.25 = 3652.5 days.
        # Let's check the timeline end of first major period
        data = self.logic.get_firdaria_data(birth_date, True, date(2000, 1, 1))
        sun_end = data['timeline'][0]['end']

        # Check at exactly sun_end
        if hasattr(sun_end, 'date'):
            sun_end_date = sun_end.date()
        else:
            sun_end_date = sun_end
        data_at_end = self.logic.get_firdaria_data(birth_date, True, sun_end_date)
        # The logic uses: if sub_start <= current_date < sub_end
        # So at sub_end it should be the NEXT major/minor period.
        self.assertEqual(data_at_end['active']['major'], const.VENUS)

if __name__ == '__main__':
    unittest.main()
