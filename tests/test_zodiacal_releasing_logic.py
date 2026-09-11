import unittest
from datetime import date
from zodiacal_releasing_logic import ZodiacalReleasingLogic
from flatlib import const

class TestZodiacalReleasingLogic(unittest.TestCase):
    def setUp(self):
        self.zr = ZodiacalReleasingLogic()

    def test_peak_signs_relative_to_fortune(self):
        # Fortune in Aries (index 0)
        # 1st = Aries (Peak)
        # 10th = Capricorn (Major Peak)
        # 7th = Libra (Peak)
        # 4th = Cancer (Peak)
        peak_map = self.zr.get_peak_signs_info(0)
        self.assertIn(const.CAPRICORN, peak_map)
        self.assertIn("Major Peak", peak_map[const.CAPRICORN])
        self.assertIn(const.ARIES, peak_map)
        self.assertIn(const.LIBRA, peak_map)
        self.assertIn(const.CANCER, peak_map)

    def test_calculate_releasing_basic(self):
        birth_str = "1990/01/01"
        start_sign = const.ARIES  # 15 years
        fortune_idx = 0  # Aries
        
        # Test age 5 (within first L1 period)
        res = self.zr.calculate_releasing(birth_str, start_sign, fortune_idx, target_date=date(1995, 1, 1))
        self.assertEqual(res['active_l1']['sign'], '牡羊座')
        self.assertEqual(res['active_l1']['is_peak'], True)
        self.assertIn('active_l2', res)
        self.assertTrue(len(res['peak_signs']) == 4)

    def test_calculate_releasing_l1_transition(self):
        birth_str = "1990/01/01"
        start_sign = const.ARIES  # 15 years -> ends ~2005/01/01
        fortune_idx = 0
        
        # At 2006/01/01, should have moved to Taurus (next sign)
        res = self.zr.calculate_releasing(birth_str, start_sign, fortune_idx, target_date=date(2006, 1, 1))
        self.assertEqual(res['active_l1']['sign'], '金牛座')

if __name__ == '__main__':
    unittest.main()
