import unittest

import safety


class SafetyTests(unittest.TestCase):
    def test_detects_self_harm(self) -> None:
        for text in ["我真的不想活了", "最近一直想 自殺", "覺得活不下去"]:
            self.assertIn("self_harm", safety.detect_risks(text), text)

    def test_detects_violence(self) -> None:
        for text in ["他昨天又打我", "我被對方掐脖子", "她威脅要殺了我", "我想申請保護令"]:
            self.assertIn("violence", safety.detect_risks(text), text)

    def test_ignores_everyday_expressions(self) -> None:
        for text in ["笑死我了", "累死了", "他打電話給我", "我們吵架了，我很生氣", "打球打得很開心"]:
            self.assertEqual(safety.detect_risks(text), set(), text)


if __name__ == "__main__":
    unittest.main()
