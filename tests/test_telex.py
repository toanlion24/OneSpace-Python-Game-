import pytest

from codequest.telex import telex_key


def type_word(keys: str) -> str:
    word = ""
    for key in keys:
        word = telex_key(word, key)
    return word


@pytest.mark.parametrize(
    ("keys", "expected"),
    [
        ("xin", "xin"),
        ("chaof", "chào"),
        ("vieejt", "việt"),
        ("nguwowif", "người"),
        ("dduwowngf", "đường"),
        ("toans", "toán"),
        ("hoaf", "hoà"),
        ("quas", "quá"),
        ("giuwax", "giữa"),
        ("tooi", "tôi"),
        ("mawtj", "mặt"),
        ("ass", "as"),
        ("cuar", "của"),
        ("thuwr", "thử"),
        ("laij", "lại"),
        ("Ddi", "Đi"),
        ("tooir", "tổi"),
        ("kej", "kẹ"),
        ("thoir", "thỏi"),
    ],
)
def test_telex_words(keys: str, expected: str) -> None:
    assert type_word(keys) == expected
