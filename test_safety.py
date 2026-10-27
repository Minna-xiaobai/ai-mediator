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

    def test_detects_english_risks(self) -> None:
        for text in ["I want to kill myself", "I've been feeling suicidal", "I don’t want to live anymore"]:
            self.assertIn("self_harm", safety.detect_risks(text), text)
        for text in ["He hit me again last night", "she threatened to kill me", "he keeps stalking me"]:
            self.assertIn("violence", safety.detect_risks(text), text)

    def test_ignores_everyday_english(self) -> None:
        for text in ["this deadline is killing me", "he hit the wall in frustration", "we had a huge fight about money", "I'm dying to see that movie"]:
            self.assertEqual(safety.detect_risks(text), set(), text)

    def test_detects_japanese_risks(self) -> None:
        for text in ["もう死にたい", "消えたいと思ってしまう", "リスカしてしまった"]:
            self.assertIn("self_harm", safety.detect_risks(text), text)
        for text in ["夫に殴られた", "彼に首を絞められた", "元恋人のストーカー被害", "DVを受けています"]:
            self.assertIn("violence", safety.detect_risks(text), text)

    def test_ignores_everyday_japanese(self) -> None:
        for text in ["疲れて死ぬほど眠い", "喧嘩してすごく腹が立った", "DVDを一緒に見た", "仕事が忙しくて大変"]:
            self.assertEqual(safety.detect_risks(text), set(), text)

    def test_help_resources_in_every_language(self) -> None:
        self.assertIn("113", safety.HELP_RESOURCES["zh"])
        self.assertIn("findahelpline.com", safety.HELP_RESOURCES["en"])
        self.assertIn("#8008", safety.HELP_RESOURCES["ja"])


if __name__ == "__main__":
    unittest.main()
