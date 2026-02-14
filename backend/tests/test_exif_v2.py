import unittest

from src.utils.exif_helper import format_shutter_speed


class TestExifHelper(unittest.TestCase):
    def test_format_shutter_speed(self):
        self.assertEqual(format_shutter_speed(0.0016666666666666668), "1/600")
        self.assertEqual(format_shutter_speed(0.0166666666), "1/60")
        self.assertEqual(format_shutter_speed(0.5), "1/2")
        self.assertEqual(format_shutter_speed("1/1000"), "1/1000")
        # Test long decimal string
        self.assertEqual(format_shutter_speed("0.0016666666666666668"), "1/600")

if __name__ == '__main__':
    unittest.main()
