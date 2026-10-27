import re
import unittest

import i18n
import legal

_PLACEHOLDER = re.compile(r"\{(\w+)\}")


class I18nTests(unittest.TestCase):
    def test_every_string_has_every_language_with_same_placeholders(self) -> None:
        for key, entry in i18n.STRINGS.items():
            self.assertEqual(set(entry), set(i18n.LANGUAGES), key)
            for lang in i18n.LANGUAGES:
                self.assertEqual(
                    set(_PLACEHOLDER.findall(entry[lang])),
                    set(_PLACEHOLDER.findall(entry["en"])),
                    f"{key} ({lang})",
                )

    def test_every_language_has_ai_name_and_help_resources(self) -> None:
        import safety

        for lang in i18n.LANGUAGES:
            self.assertIn(lang, i18n.AI_LANGUAGE_NAMES)
            self.assertIn(lang, safety.HELP_RESOURCES)

    def test_storage_error_codes_are_translated(self) -> None:
        with open("storage.py", encoding="utf-8") as source:
            codes = set(re.findall(r'StorageError\("(\w+)"', source.read()))
        self.assertTrue(codes)
        self.assertLessEqual(codes, set(i18n.STRINGS))

    def test_legal_documents_format_in_both_languages(self) -> None:
        for document in (legal.PRIVACY, legal.TERMS):
            for lang in i18n.LANGUAGES:
                text = document[lang].format(contact="a@b.c", updated=legal.UPDATED)
                self.assertIn("a@b.c", text)

    def test_language_from_locale(self) -> None:
        self.assertEqual(i18n.language_from_locale("zh-TW"), "zh")
        self.assertEqual(i18n.language_from_locale("zh-Hans-CN"), "zh")
        self.assertEqual(i18n.language_from_locale("en-US"), "en")
        self.assertEqual(i18n.language_from_locale("ja-JP"), "ja")
        self.assertEqual(i18n.language_from_locale("ko-KR"), "en")
        self.assertEqual(i18n.language_from_locale(None), "en")


if __name__ == "__main__":
    unittest.main()
