"""Tests for logged-out detection, the no-ads alert and login failure reporting."""

from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.alo.actions import looks_logged_out, get_submit_selectors


def test_submit_selectors_scoped_to_login_form():
    selectors = get_submit_selectors()
    assert selectors[0] == "#btn-login"
    for sel in selectors:
        assert sel.startswith("#") or sel.startswith("form:has(input[type=\"password\"])")
    assert 'button[type="submit"]' not in selectors
    assert 'input[type="submit"]' not in selectors
from app.services.runner import AdBumpRunner


@pytest.mark.parametrize("url, has_pw, expected", [
    ("https://www.alo.bg/login.php", True, True),
    ("https://www.alo.bg/LOGIN.php?x=1", True, True),
    ("https://www.alo.bg/login.php", False, False),
    ("https://www.alo.bg/user_edit_panel.php", True, False),
    ("https://www.alo.bg/user_edit_panel.php", False, False),
    (None, True, False),
])
def test_looks_logged_out(url, has_pw, expected):
    assert looks_logged_out(url, has_pw) is expected


def build_runner(monkeypatch, login_ok, ads, **actions_attrs):
    runner = AdBumpRunner()
    runner.browser_manager = MagicMock()
    runner.browser_manager.start = AsyncMock()
    runner.browser_manager.close = AsyncMock()
    page = MagicMock()
    page.wait_for_timeout = AsyncMock()
    runner.browser_manager.get_page = MagicMock(return_value=page)
    runner.notifier = MagicMock()

    actions = MagicMock()
    actions.login = AsyncMock(return_value=login_ok)
    actions.get_active_ads = AsyncMock(return_value=ads)
    for key, value in actions_attrs.items():
        setattr(actions, key, value)
    monkeypatch.setattr("app.services.runner.AloActions", lambda p: actions)
    return runner


async def test_no_ads_sends_alert_not_report(monkeypatch):
    runner = build_runner(
        monkeypatch, True, [],
        last_ads_page_info={
            "url": "https://www.alo.bg/login.php?<x>",
            "title": "Вход <b>",
            "logged_out": True,
        },
    )
    await runner.run()

    runner.notifier.send_report.assert_called_once()
    text = runner.notifier.send_report.call_args[0][0]
    assert "Не найдено ни одного объявления" in text
    assert "Похоже, бот не вошёл в аккаунт" in text
    assert "logs/no_ads.png" in text
    assert "Отчёт о поднятии" not in text
    # page-derived text is escaped
    assert "&lt;x&gt;" in text
    assert "Вход &lt;b&gt;" in text


async def test_no_ads_not_logged_out_hint(monkeypatch):
    runner = build_runner(
        monkeypatch, True, [],
        last_ads_page_info={"url": "https://www.alo.bg/my", "title": "Мои", "logged_out": False},
    )
    await runner.run()

    text = runner.notifier.send_report.call_args[0][0]
    assert "Проверьте, есть ли активные объявления" in text
    assert "не вошёл" not in text


async def test_login_failure_report_includes_reason(monkeypatch):
    runner = build_runner(
        monkeypatch, False, [],
        last_login_failure="URL: https://www.alo.bg/login.php; капча: да <i>",
    )
    await runner.run()

    runner.notifier.send_report.assert_called_once()
    text = runner.notifier.send_report.call_args[0][0]
    assert "Не удалось выполнить вход на сайт" in text
    assert "капча: да" in text
    assert "&lt;i&gt;" in text
