import unittest

from baristaos.app import BaristaOS


class TestBaristaOS(unittest.TestCase):
    def test_baristaos(self):
        se = BaristaOS([], None, None)
        self.assertRaises(ValueError, se.run)


if __name__ == "__main__":
    unittest.main()
