import unittest
from unittest.mock import MagicMock
from aspects_logic import AspectsLogic
from flatlib import const

class TestAspectsLogic(unittest.TestCase):
    def setUp(self):
        self.logic = AspectsLogic()

    def test_check_reception(self):
        # Mars in Leo (Sun rules Leo)
        # Sun in Aries (Mars rules Aries)
        # This is mutual reception

        trans_planets = {const.MARS: '火星', const.SUN: '太陽'}

        # Mars at 120 (Leo 0)
        # Sun at 0 (Aries 0)
        res = self.logic.check_reception(const.MARS, 120, const.SUN, 0, trans_planets)
        self.assertEqual(res, "互容 (Mutual Reception)")

        # Mars in Leo (Sun rules Leo)
        # Sun in Taurus (Venus rules Taurus)
        # Sun receives Mars (Sun is P2)
        res = self.logic.check_reception(const.MARS, 120, const.SUN, 30, trans_planets)
        self.assertEqual(res, "太陽 接納 火星")

        # Mars in Taurus (Venus rules Taurus)
        # Sun in Aries (Mars rules Aries)
        # Mars receives Sun (Mars is P1)
        res = self.logic.check_reception(const.MARS, 30, const.SUN, 0, trans_planets)
        self.assertEqual(res, "火星 接納 太陽")

if __name__ == '__main__':
    unittest.main()
