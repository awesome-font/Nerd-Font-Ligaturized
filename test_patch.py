import unittest
from patch import clean_font_name

class TestCleanFontName(unittest.TestCase):
    def test_basic_suffixes(self):
        test_cases = [
            ("FiraCode-Bold.ttf", "FiraCode"),
            ("JetBrains-Regular.otf", "JetBrains"),
            ("Hack_Italic.ttf", "Hack"),
            ("SourceCode.bold.ttf", "SourceCode"),
            ("MonoLisa-Regular.ttf", "MonoLisa")
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                self.assertEqual(clean_font_name(input_name), expected)
                
    def test_additional_styles(self):
        test_cases = [
            ("FiraCode-Medium.ttf", "FiraCode-Medium"),
            ("JetBrains-ExtraBold.otf", "JetBrains-ExtraBold"),
            ("Hack-ExtraLight.ttf", "Hack-ExtraLight"),
            ("SourceCode-Light.ttf", "SourceCode-Light"),
            ("MonoLisa-SemiBold.ttf", "MonoLisa-SemiBold")
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                self.assertEqual(clean_font_name(input_name), expected)
    
    def test_no_style(self):
        test_cases = [
            ("FiraCode.ttf", "FiraCode"),
            ("JetBrains.otf", "JetBrains"),
            ("SimpleFont.ttf", "SimpleFont")
        ]
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                self.assertEqual(clean_font_name(input_name), expected)

if __name__ == '__main__':
    unittest.main()