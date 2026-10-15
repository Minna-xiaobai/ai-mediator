"""Keyword-based safety screening for self-harm and interpersonal violence.

This is a conservative first layer, not a clinical assessment. It favours
showing help resources over missing a risk, and avoids single characters
such as「死」that appear in everyday expressions (e.g.「笑死」).
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

_SELF_HARM_RE = re.compile("|".join(_SELF_HARM_PATTERNS))
_VIOLENCE_RE = re.compile("|".join(_VIOLENCE_PATTERNS))

HELP_RESOURCES = """\
**如果你或他人有立即危險，請撥打 110（警察）或 119（救護）。**

- **113 保護專線**（24 小時）：家庭暴力、性侵害、兒少保護
- **1925 安心專線**（24 小時，免付費）：情緒困擾、想傷害自己
- **1995 生命線**／**1980 張老師專線**：情緒支持與陪談

你不需要獨自面對。這個工具無法處理緊急或安全問題，請優先聯繫專業協助。
"""

SAFETY_SYSTEM_PROMPT = (
    "若使用者提到想傷害自己、自殺念頭，或正遭受暴力、威脅、控制、跟蹤、性暴力，"
    "請以安全為第一優先：溫和肯定對方說出來的勇氣，詢問其目前是否安全，"
    "鼓勵聯繫 110、113 保護專線或 1925 安心專線，"
    "且不要建議與施暴者協商、調解或分享摘要給對方。"
)


def detect_risks(text: str) -> set[RiskType]:
    """Return the risk categories whose keywords appear in text."""
    normalized = re.sub(r"\s+", "", text)
    risks: set[RiskType] = set()
    if _SELF_HARM_RE.search(normalized):
        risks.add("self_harm")
    if _VIOLENCE_RE.search(normalized):
        risks.add("violence")
    return risks
