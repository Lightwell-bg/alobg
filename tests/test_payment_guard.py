"""Tests for the payment marker detection helper."""

import pytest

from app.alo.actions import is_payment_text, classify_dialog_text


@pytest.mark.parametrize("text, expected", [
    ("Съобщение\nClose\nТази обява е обновявана или публикувана днес\nОК", "already_updated"),
    ("Цената е 2.50 лв", "payment"),
    ("Обявата е обновена успешно", "other"),
    ("Съобщение\nClose", "other"),
    ("", "none"),
    (None, "none"),
    ("   ", "none"),
])
def test_classify_dialog_text(text, expected):
    assert classify_dialog_text(text) == expected


def test_short_markers_need_word_boundary():
    assert not is_payment_text("Топло е днес")
    assert is_payment_text("Цена 5лв")


@pytest.mark.parametrize("text", [
    "Цена: 2.50 лв",
    "Платете 1 EUR",
    "Изпратете SMS",
    "VIP обява",
    "ТОП позиция",
    "Плащане с карта",
    "Купи кредити",
    "Промо пакет",
    "Само 1.00 €",
    "10 евро",
])
def test_payment_text_detected(text):
    assert is_payment_text(text)


@pytest.mark.parametrize("text", [
    "OK",
    "Обявата е обновена успешно",
    "Потвърди",
    "",
    None,
])
def test_non_payment_text(text):
    assert not is_payment_text(text)
