import unittest

from src.utils.exif_helper import format_shutter_speed


class TestExifHelper(unittest.TestCase):
    def test_format_shutter_speed_float(self):
        # 1/600 approx 0.0016666
        self.assertEqual(format_shutter_speed(0.0016666666666666668), "1/600")
        
        # 1/60 approx
        self.assertEqual(format_shutter_speed(0.0166666666), "1/60")
        
        # 0.5 -> 1/2
        self.assertEqual(format_shutter_speed(0.5), "1/2")

    def test_format_shutter_speed_long_string(self):
        # Long string representation
        long_str = "0.0016666666666666668"
        self.assertEqual(format_shutter_speed(long_str), "1/600")

    def test_format_shutter_speed_normal(self):
        self.assertEqual(format_shutter_speed("1/1000"), "1/1000")
        self.assertEqual(format_shutter_speed(0.001), "1/1000")

if __name__ == '__main__':
    unittest.main()
