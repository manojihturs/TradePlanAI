"""Tests for SubscriptionManager."""

from __future__ import annotations

from trading_engine.market_data.instrument_resolver import InstrumentKey
from trading_engine.market_data.subscription_manager import SubscriptionManager


class TestSubscribe:
    def test_subscribing_new_instrument_returns_true(
        self, sample_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        assert manager.subscribe(sample_instrument) is True
        assert manager.is_subscribed(sample_instrument)

    def test_subscribing_twice_returns_false_second_time(
        self, sample_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        manager.subscribe(sample_instrument)
        assert manager.subscribe(sample_instrument) is False

    def test_starts_empty(self) -> None:
        assert len(SubscriptionManager()) == 0


class TestUnsubscribe:
    def test_unsubscribing_active_instrument_returns_true(
        self, sample_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        manager.subscribe(sample_instrument)
        assert manager.unsubscribe(sample_instrument) is True
        assert not manager.is_subscribed(sample_instrument)

    def test_unsubscribing_inactive_instrument_returns_false(
        self, sample_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        assert manager.unsubscribe(sample_instrument) is False


class TestActiveSubscriptions:
    def test_lists_every_active_instrument(
        self, sample_instrument: InstrumentKey, another_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        manager.subscribe(sample_instrument)
        manager.subscribe(another_instrument)
        assert set(manager.active_subscriptions()) == {sample_instrument, another_instrument}
        assert len(manager) == 2

    def test_removed_instrument_excluded(
        self, sample_instrument: InstrumentKey, another_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        manager.subscribe(sample_instrument)
        manager.subscribe(another_instrument)
        manager.unsubscribe(sample_instrument)
        assert manager.active_subscriptions() == (another_instrument,)


class TestClear:
    def test_clear_removes_all_subscriptions(
        self, sample_instrument: InstrumentKey, another_instrument: InstrumentKey
    ) -> None:
        manager = SubscriptionManager()
        manager.subscribe(sample_instrument)
        manager.subscribe(another_instrument)
        manager.clear()
        assert len(manager) == 0
        assert manager.active_subscriptions() == ()
