"""Built-in Vietnamese Telex input method.

Typing rules:  aa=â  aw=ă  ee=ê  oo=ô  ow=ơ  uw=ư  w=ư  dd=đ
Tones:         s=sắc  f=huyền  r=hỏi  x=ngã  j=nặng  z=xoá dấu
Pressing the same tone key twice removes the tone and keeps the letter (e.g. "ass" → "as").
"""

from __future__ import annotations

TONE_KEYS = "sfrxj"
TONED_VOWELS: dict[str, str] = {
    "a": "aáàảãạ",
    "ă": "ăắằẳẵặ",
    "â": "âấầẩẫậ",
    "e": "eéèẻẽẹ",
    "ê": "êếềểễệ",
    "i": "iíìỉĩị",
    "o": "oóòỏõọ",
    "ô": "ôốồổỗộ",
    "ơ": "ơớờởỡợ",
    "u": "uúùủũụ",
    "ư": "ưứừửữự",
    "y": "yýỳỷỹỵ",
}
MARKED_BASES = set("ăâêôơư")

CHAR_TO_BASE_TONE: dict[str, tuple[str, int]] = {}
for _base, _forms in TONED_VOWELS.items():
    for _tone, _char in enumerate(_forms):
        CHAR_TO_BASE_TONE[_char] = (_base, _tone)
        CHAR_TO_BASE_TONE[_char.upper()] = (_base.upper(), _tone)


def is_vowel(char: str) -> bool:
    return char in CHAR_TO_BASE_TONE


def split_char(char: str) -> tuple[str, int]:
    return CHAR_TO_BASE_TONE.get(char, (char, 0))


def compose(base: str, tone: int) -> str:
    lower = base.lower()
    if lower not in TONED_VOWELS:
        return base
    char = TONED_VOWELS[lower][tone]
    return char.upper() if base.isupper() else char


def _vowel_span(word: str) -> tuple[int, int] | None:
    """Return [start, end) of the last vowel cluster, treating qu/gi as consonants."""
    end = None
    for index in range(len(word) - 1, -1, -1):
        if is_vowel(word[index]):
            end = index + 1
            break
    if end is None:
        return None
    start = end - 1
    while start > 0 and is_vowel(word[start - 1]):
        start -= 1
    head = word[: start + 1].lower()
    if end - start > 1 and head.endswith(("qu", "gi")):
        base_start = split_char(word[start])[0].lower()
        if base_start in ("u", "i"):
            start += 1
    return start, end


def _tone_position(word: str) -> int | None:
    span = _vowel_span(word)
    if span is None:
        return None
    start, end = span
    bases = [split_char(char)[0].lower() for char in word[start:end]]
    marked = [index for index, base in enumerate(bases) if base in MARKED_BASES]
    if marked:
        return start + marked[-1]
    length = end - start
    if length == 1:
        return start
    if end < len(word):
        return end - 1
    if length == 3:
        return start + 1
    if "".join(bases) in ("oa", "oe", "uy"):
        return start + 1
    return start


def current_tone(word: str) -> int:
    for char in word:
        tone = split_char(char)[1]
        if tone:
            return tone
    return 0


def strip_tones(word: str) -> str:
    return "".join(compose(*_strip(char)) for char in word)


def _strip(char: str) -> tuple[str, int]:
    base, _tone = split_char(char)
    return base, 0


def apply_tone(word: str, tone: int) -> str:
    plain = strip_tones(word)
    if tone == 0:
        return plain
    position = _tone_position(plain)
    if position is None:
        return plain
    base, _ = split_char(plain[position])
    return plain[:position] + compose(base, tone) + plain[position + 1 :]


def _replace_base(word: str, index: int, new_base: str) -> str:
    base, tone = split_char(word[index])
    if base.isupper():
        new_base = new_base.upper()
    return word[:index] + compose(new_base, tone) + word[index + 1 :]


def _modify_vowels(word: str, key: str) -> str | None:
    span = _vowel_span(word)
    lower_key = key.lower()
    if lower_key == "w":
        if span is None:
            return None
        start, end = span
        bases = [split_char(char)[0].lower() for char in word[start:end]]
        joined = "".join(bases)
        if "uo" in joined:
            offset = joined.index("uo")
            word = _replace_base(word, start + offset, "ư")
            return _replace_base(word, start + offset + 1, "ơ")
        for index in range(end - 1, start - 1, -1):
            base = split_char(word[index])[0].lower()
            mapping = {"a": "ă", "o": "ơ", "u": "ư"}
            if base in mapping:
                return _replace_base(word, index, mapping[base])
        return None

    if span is None:
        return None
    start, end = span
    for index in range(end - 1, start - 1, -1):
        base = split_char(word[index])[0].lower()
        if base == lower_key:
            return _replace_base(word, index, {"a": "â", "e": "ê", "o": "ô"}[lower_key])
    return None


def telex_key(word: str, key: str) -> str:
    """Return the new word after typing `key` at the end of `word`."""
    lower_key = key.lower()
    tone = current_tone(word)

    if lower_key in TONE_KEYS and _vowel_span(word) is not None:
        new_tone = TONE_KEYS.index(lower_key) + 1
        if tone == new_tone:
            return apply_tone(word, 0) + key
        return apply_tone(word, new_tone)

    if lower_key == "z" and tone:
        return apply_tone(word, 0)

    if lower_key == "d" and word and word[-1] in "dD" and len(word) == 1:
        return "Đ" if word[-1] == "D" else "đ"
    if lower_key == "d" and word[:1] in ("d", "D") and "đ" not in word.lower():
        return ("Đ" if word[0] == "D" else "đ") + word[1:]

    if lower_key in "aeow":
        modified = _modify_vowels(word, key)
        if modified is not None and modified != word:
            return apply_tone(modified, tone) if tone else modified
        if lower_key == "w":
            return word + ("Ư" if key.isupper() else "ư")

    appended = word + key
    return apply_tone(appended, tone) if tone else appended


def is_word_char(char: str) -> bool:
    return char.isalpha()
