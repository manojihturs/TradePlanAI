"""Tests for CalculationContext."""

from __future__ import annotations

import dataclasses
from datetime import datetime

import pytest

from trading_engine.calculators.context import CalculationContext
from trading_engine.calculators.exceptions import CalculationError
from trading_engine.domain.market_context import MarketContext
from trading_engine.domain.session_state import SessionState


class TestConstructorValidation:
    def test_valid_construction_with_defaults(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = CalculationContext(sample_market_context, sample_session_state)
        assert context.market_context is sample_market_context
        assert context.session_state is sample_session_state
        assert context.configuration == {}
        assert isinstance(context.calculation_timestamp, datetime)

    def test_configuration_can_be_supplied(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = CalculationContext(
            sample_market_context, sample_session_state, configuration={"lookback": 5}
        )
        assert context.configuration == {"lookback": 5}

    def test_calculation_timestamp_can_be_supplied(
        self,
        sample_market_context: MarketContext,
        sample_session_state: SessionState,
        valid_datetime: datetime,
    ) -> None:
        context = CalculationContext(
            sample_market_context, sample_session_state, calculation_timestamp=valid_datetime
        )
        assert context.calculation_timestamp == valid_datetime


class TestInvalidConstructorValues:
    def test_none_market_context_raises(self, sample_session_state: SessionState) -> None:
        with pytest.raises(CalculationError, match="market_context must not be None"):
            CalculationContext(None, sample_session_state)  # type: ignore[arg-type]

    def test_none_session_state_raises(self, sample_market_context: MarketContext) -> None:
        with pytest.raises(CalculationError, match="session_state must not be None"):
            CalculationContext(sample_market_context, None)  # type: ignore[arg-type]

    def test_none_calculation_timestamp_raises(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        with pytest.raises(CalculationError, match="calculation_timestamp must not be None"):
            CalculationContext(
                sample_market_context, sample_session_state, calculation_timestamp=None  # type: ignore[arg-type]
            )


class TestEquality:
    def test_equal_values_are_equal(
        self,
        sample_market_context: MarketContext,
        sample_session_state: SessionState,
        valid_datetime: datetime,
    ) -> None:
        a = CalculationContext(
            sample_market_context, sample_session_state, calculation_timestamp=valid_datetime
        )
        b = CalculationContext(
            sample_market_context, sample_session_state, calculation_timestamp=valid_datetime
        )
        assert a == b


class TestImmutability:
    def test_cannot_reassign_configuration(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = CalculationContext(sample_market_context, sample_session_state)
        with pytest.raises(dataclasses.FrozenInstanceError):
            context.configuration = {}  # type: ignore[misc]


class TestEdgeCases:
    def test_each_construction_gets_a_default_timestamp(
        self, sample_market_context: MarketContext, sample_session_state: SessionState
    ) -> None:
        context = CalculationContext(sample_market_context, sample_session_state)
        assert context.calculation_timestamp is not None
