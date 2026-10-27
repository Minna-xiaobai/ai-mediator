"""Keyword-based safety screening for self-harm and interpersonal violence.

This is a conservative first layer, not a clinical assessment. It favours
showing help resources over missing a risk, and avoids single characters
such as「死」that appear in everyday expressions (e.g.「笑死」).
Chinese and English patterns are both checked, whatever the interface language.
"""

import re
from typing import Literal

RiskType = Literal["self_harm", "violence"]

_SELF_HARM_PATTERNS = [
    r"自殺", r"自盡", r"輕生", r"尋死", r"想死", r"去死好了", r"不想活",
    r"活不下去", r"活著沒(有)?意義", r"結束(我的)?生命", r"結束自己",
    r"了結(自己|生命)", r"割腕", r"跳樓", r"燒炭", r"上吊", r"吞藥",
    r"傷害自己", r"自殘", r"消失(就好|算了)", r"一了百了",
]

_VIOLENCE_PATTERNS = [
    r"家暴", r"家庭暴力", r"(打|揍|踢|推|掐|勒)(了)?我", r"被(他|她|對方)?(打|揍|踢|掐|勒)",
    r"掐(我的)?脖子", r"動手打", r"拿刀", r"威脅要?(殺|打|傷害)",
    r"要殺(了)?(我|你|他|她)", r"殺了(我|你|他|她)", r"恐嚇",
    r"跟蹤(我)?", r"監控我", r"不准我(出門|見|聯絡)", r"關(起來|住我)",
    r"性侵", r"強迫(我)?(發生)?性", r"逼我(發生)?性", r"保護令",
    r"怕(他|她|對方)會?(傷害|打)",
]

_SELF_HARM_PATTERNS_EN = [
    r"suicid(e|al)", r"kill(ing)? myself", r"end(ing)? (my|it) (life|all)",
    r"take my (own )?life", r"(want|wanna) to die", r"don'?t want to (live|be alive)",
    r"better off dead", r"no reason to live", r"self[- ]?harm",
    r"(cut|hurt|harm)(ting)? myself", r"overdose",
]

_VIOLENCE_PATTERNS_EN = [
    r"domestic (violence|abuse)", r"(hit|hits|punch(ed|es)?|kick(ed|s)?|slap(ped|s)?|beat|beats|chok(ed|es)|strangl(ed|es)) me",
    r"(physically|sexually) abus(e|es|ed|ive)", r"threaten(ed|s)? to (kill|hurt|beat)",
    r"(going|gonna) to kill (me|you|him|her)", r"stalk(ing|s|ed)? me",
    r"(won'?t|doesn'?t|does not|will not) let me (leave|go out|see)", r"lock(ed|s)? me (in|up)",
    r"rap(e|ed)", r"sexual(ly)? assault", r"forc(ed|es|ing) me to have sex",
    r"restraining order", r"protection order", r"afraid (he|she|they)('ll| will) hurt me",
]

_SELF_HARM_PATTERNS_JA = [
    r"死にたい", r"消えたい", r"生きていたくない", r"生きる意味(が|は)?(ない|無い)",
    r"生きていても意味", r"命を絶", r"リストカット", r"リスカ", r"自傷",
    r"飛び降り(たい|よう)", r"首を(吊|つ)", r"楽に死",
]

_VIOLENCE_PATTERNS_JA = [
    r"DV(?!D)", r"ＤＶ", r"殴(られ|ってくる|る(んです|の))", r"蹴られ", r"叩かれ",
    r"首を絞め", r"暴力を(振|ふ)る", r"脅(され|迫)", r"殺(すと|される|してやる)",
    r"ストーカー", r"つきまと", r"監視されて", r"外出させてもらえない", r"閉じ込め",
    r"レイプ", r"性的暴行", r"無理(やり|矢理)(性|関係)", r"保護命令",
]

_SELF_HARM_RE = re.compile("|".join(_SELF_HARM_PATTERNS + _SELF_HARM_PATTERNS_JA))
_VIOLENCE_RE = re.compile("|".join(_VIOLENCE_PATTERNS + _VIOLENCE_PATTERNS_JA))
_SELF_HARM_EN_RE = re.compile(r"\b(" + "|".join(_SELF_HARM_PATTERNS_EN) + r")\b", re.IGNORECASE)
_VIOLENCE_EN_RE = re.compile(r"\b(" + "|".join(_VIOLENCE_PATTERNS_EN) + r")\b", re.IGNORECASE)

HELP_RESOURCES_ZH = """\
**如果你或他人有立即危險，請撥打 110（警察）或 119（救護）。**

- **113 保護專線**（24 小時）：家庭暴力、性侵害、兒少保護
- **1925 安心專線**（24 小時，免付費）：情緒困擾、想傷害自己
- **1995 生命線**／**1980 張老師專線**：情緒支持與陪談

你不需要獨自面對。這個工具無法處理緊急或安全問題，請優先聯繫專業協助。
"""

HELP_RESOURCES_EN = """\
**If you or someone else is in immediate danger, call your local emergency number now.**

- **Find a free, confidential helpline in your country:** [findahelpline.com](https://findahelpline.com)
- **US:** 988 Suicide & Crisis Lifeline (call or text 988); National Domestic Violence Hotline 1-800-799-7233
- **UK & Ireland:** Samaritans 116 123
- **Taiwan:** 110 (police), 113 (protection hotline), 1925 (mental health)

You don't have to face this alone. This tool cannot handle emergencies or safety issues; please reach out to professional help first.
"""

HELP_RESOURCES_JA = """\
**あなたや他の人に差し迫った危険がある場合は、すぐに 110 番（警察）または 119 番（救急）に電話してください。**

- **いのちの電話**：0570-783-556（ナビダイヤル）— つらい気持ち、死にたい気持ち
- **よりそいホットライン**（24 時間・無料）：0120-279-338
- **DV 相談ナビ**：#8008 ／ **DV 相談＋**（24 時間）：0120-279-889
- **こころの健康相談統一ダイヤル**：0570-064-556
- 日本国外の方：[findahelpline.com](https://findahelpline.com)

一人で抱え込まないでください。このツールは緊急事態や安全の問題には対応できません。まず専門の窓口に相談してください。
"""

HELP_RESOURCES = {"zh": HELP_RESOURCES_ZH, "en": HELP_RESOURCES_EN, "ja": HELP_RESOURCES_JA}

SAFETY_SYSTEM_PROMPT = (
    " If the user mentions wanting to hurt themselves, suicidal thoughts, or "
    "experiencing violence, threats, coercive control, stalking, or sexual "
    "violence, put safety first: gently acknowledge their courage in saying it, "
    "ask whether they are safe right now, and encourage them to contact local "
    "emergency services or a crisis line (Taiwan: 110, 113 protection hotline, "
    "1925; Japan: 110, Inochi no Denwa 0570-783-556, DV soudan #8008; US: 988; "
    "elsewhere: findahelpline.com). Do not suggest negotiating "
    "or mediating with an abuser, or sharing a summary with them."
)


def detect_risks(text: str) -> set[RiskType]:
    """Return the risk categories whose keywords appear in text."""
    normalized = re.sub(r"\s+", "", text)
    risks: set[RiskType] = set()
    if _SELF_HARM_RE.search(normalized):
        risks.add("self_harm")
    if _VIOLENCE_RE.search(normalized):
        risks.add("violence")
    spaced = re.sub(r"\s+", " ", text).replace("\u2019", "'")
    if _SELF_HARM_EN_RE.search(spaced):
        risks.add("self_harm")
    if _VIOLENCE_EN_RE.search(spaced):
        risks.add("violence")
    return risks
