"""Tests for the payment marker detection helper."""

import pytest

from app.alo.actions import is_payment_text


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
