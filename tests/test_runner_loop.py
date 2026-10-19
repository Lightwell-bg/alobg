"""Tests for the AdBumpRunner main loop using fakes (no real browser)."""

from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.runner import AdBumpRunner


def make_ads(n):
    return [{"title": f"ad{i}", "button_index": i} for i in range(n)]


def build_runner(monkeypatch, get_ads, bump):
    runner = AdBumpRunner()
    runner.browser_manager = MagicMock()
    runner.browser_manager.start = AsyncMock()
    runner.browser_manager.close = AsyncMock()
    page = MagicMock()
    page.wait_for_timeout = AsyncMock()
    runner.browser_manager.get_page = MagicMock(return_value=page)
    runner.notifier = MagicMock()

    actions = MagicMock()
    actions.login = AsyncMock(return_value=True)
    actions.get_active_ads = AsyncMock(side_effect=get_ads)
    actions.bump_ad = AsyncMock(side_effect=bump)

    monkeypatch.setattr("app.services.runner.AloActions", lambda p: actions)
    return runner, actions


async def test_stuck_list_terminates_with_cap(monkeypatch):
    """Bump always succeeds but the list never shrinks: loop must stop."""
    positions = []

    async def get_ads():
        return make_ads(5)

    async def bump(ad):
        positions.append(ad["button_index"])
        return True, "Обновлено"

    runner, actions = build_runner(monkeypatch, get_ads, bump)
    await runner.run()

    # positions advance 0..4 and then loop ends (pos reaches len)
    assert positions == [0, 1, 2, 3, 4]
    assert actions.bump_ad.await_count <= 2 * 5 + 5


async def test_three_unconfirmed_stops_early(monkeypatch):
    async def get_ads():
        return make_ads(8)

    async def bump(ad):
        return False, "unconfirmed"

    runner, actions = build_runner(monkeypatch, get_ads, bump)
    await runner.run()

    assert actions.bump_ad.await_count == 3
    runner.notifier.send_report.assert_called_once()
    assert "Не подтверждено" in runner.notifier.send_report.call_args[0][0]


async def test_normal_case_all_bumped(monkeypatch):
    state = {"n": 4}

    async def get_ads():
        return make_ads(state["n"])

    async def bump(ad):
        state["n"] -= 1
        return True, "Обновлено"

    runner, actions = build_runner(monkeypatch, get_ads, bump)
    await runner.run()

    assert actions.bump_ad.await_count == 4
    assert [r["status"] for r in runner.results] == ["Обновлено"] * 4


async def test_four_disabled_one_active(monkeypatch):
    async def get_ads():
        return make_ads(5)

    async def bump(ad):
        if ad["button_index"] == 4:
            return True, "Обновлено"
        return False, "already_updated_today"

    runner, actions = build_runner(monkeypatch, get_ads, bump)
    await runner.run()

    assert actions.bump_ad.await_count == 5
    statuses = [r["status"] for r in runner.results]
    assert statuses.count("Обновлено") == 1
    assert statuses.count("Уже обновлено сегодня") == 4
    report = runner.notifier.send_report.call_args[0][0]
    assert "<b>Успешно поднято:</b> 1" in report


async def test_all_disabled_sends_already_updated_report(monkeypatch):
    async def get_ads():
        return make_ads(3)

    async def bump(ad):
        return False, "already_updated_today"

    runner, actions = build_runner(monkeypatch, get_ads, bump)
    await runner.run()

    assert actions.bump_ad.await_count == 3
    report = runner.notifier.send_report.call_args[0][0]
    assert "Все объявления уже обновлены" in report


async def test_payment_dialog_skipped_not_bumped(monkeypatch):
    async def get_ads():
        return make_ads(2)

    async def bump(ad):
        return False, "payment_dialog"

    runner, actions = build_runner(monkeypatch, get_ads, bump)
    await runner.run()

    assert actions.bump_ad.await_count == 2
    assert all("платный диалог" in r["status"] for r in runner.results)
    report = runner.notifier.send_report.call_args[0][0]
    assert "<b>Успешно поднято:</b> 0" in report
