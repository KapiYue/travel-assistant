"""Offline tests for the first travel-assistant workflow loop."""

from __future__ import annotations

import os
import unittest
from datetime import date
from unittest.mock import Mock, patch

from pydantic import ValidationError

from backend.travel_assistant.extraction import (
    EmptyTravelRequestError,
    ModelConfigurationError,
    ModelInvocationError,
    StructuredOutputValidationError,
    create_structured_extractor,
    extract_travel_request,
)
from backend.travel_assistant.models import TravelRequest


class FakeExtractor:
    """An offline substitute for the LangChain model runnable."""

    def __init__(self, result: object | Exception) -> None:
        self.result = result
        self.input_value: dict[str, str] | None = None

    def invoke(self, input_value: dict[str, str]) -> object:
        self.input_value = input_value
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


class TravelRequestModelTests(unittest.TestCase):
    def test_calculates_missing_fields_and_unique_end_date(self) -> None:
        request = TravelRequest(
            destination="杭州",
            start_date=date(2026, 11, 10),
            days=3,
            traveler_count=2,
            budget="5000 元",
            preferences=["自然风景", "慢节奏"],
            constraints=["行程不要太赶"],
        )

        self.assertEqual(request.end_date, date(2026, 11, 12))
        self.assertEqual(request.missing_fields, [])
        self.assertEqual(request.preferences, ["自然风景", "慢节奏"])
        self.assertEqual(request.constraints, ["行程不要太赶"])

    def test_does_not_infer_parent_trip_count_or_required_values(self) -> None:
        request = TravelRequest(
            destination="杭州",
            preferences=["轻松", "自然风景"],
            constraints=["父母同行"],
        )

        self.assertIsNone(request.traveler_count)
        self.assertEqual(
            request.missing_fields,
            ["start_date", "days", "traveler_count", "budget"],
        )

    def test_rejects_non_positive_counts_and_reversed_dates(self) -> None:
        with self.assertRaises(ValidationError):
            TravelRequest(days=0)
        with self.assertRaises(ValidationError):
            TravelRequest(traveler_count=-1)
        with self.assertRaises(ValidationError):
            TravelRequest(start_date=date(2026, 11, 12), end_date=date(2026, 11, 10))

    def test_uses_independent_default_lists(self) -> None:
        first = TravelRequest()
        second = TravelRequest()

        first.preferences.append("美食")
        self.assertEqual(second.preferences, [])


class ExtractionTests(unittest.TestCase):
    def test_extracts_complete_request_from_structured_model_result(self) -> None:
        extractor = FakeExtractor(
            {
                "destination": "杭州",
                "start_date": "2026-11-10",
                "end_date": None,
                "days": 3,
                "traveler_count": 2,
                "budget": "5000 元",
                "preferences": ["自然风景", "慢节奏"],
                "constraints": ["行程不要太赶"],
            }
        )

        request = extract_travel_request("我和朋友两个人计划去杭州玩。", extractor)

        self.assertEqual(request.destination, "杭州")
        self.assertEqual(request.start_date, date(2026, 11, 10))
        self.assertEqual(request.end_date, date(2026, 11, 12))
        self.assertEqual(request.missing_fields, [])
        self.assertEqual(extractor.input_value, {"user_input": "我和朋友两个人计划去杭州玩。"})

    def test_preserves_known_values_for_an_incomplete_request(self) -> None:
        extractor = FakeExtractor(
            {
                "destination": "杭州",
                "start_date": None,
                "end_date": None,
                "days": None,
                "traveler_count": None,
                "budget": None,
                "preferences": ["轻松", "自然风景"],
                "constraints": ["父母同行"],
            }
        )

        request = extract_travel_request("想带父母去杭州轻松玩。", extractor)

        self.assertIsNone(request.traveler_count)
        self.assertEqual(request.constraints, ["父母同行"])
        self.assertEqual(
            request.missing_fields,
            ["start_date", "days", "traveler_count", "budget"],
        )

    def test_empty_input_does_not_create_or_call_a_model(self) -> None:
        with patch("backend.travel_assistant.extraction.create_structured_extractor") as create_extractor:
            with self.assertRaisesRegex(EmptyTravelRequestError, "请输入旅行需求"):
                extract_travel_request("   ")

        create_extractor.assert_not_called()

    def test_invalid_structured_result_is_reported_without_partial_request(self) -> None:
        extractor = FakeExtractor(
            {
                "destination": "杭州",
                "start_date": None,
                "end_date": None,
                "days": 0,
                "traveler_count": 2,
                "budget": "5000 元",
                "preferences": [],
                "constraints": [],
            }
        )

        with self.assertRaisesRegex(StructuredOutputValidationError, "Pydantic 校验"):
            extract_travel_request("去杭州玩", extractor)

    def test_model_failure_is_reported_without_provider_details(self) -> None:
        extractor = FakeExtractor(ConnectionError("token=secret-value"))

        with self.assertRaises(ModelInvocationError) as context:
            extract_travel_request("去杭州玩", extractor)

        self.assertNotIn("secret-value", str(context.exception))


class ModelConfigurationTests(unittest.TestCase):
    @patch("backend.travel_assistant.extraction.load_dotenv")
    def test_missing_model_settings_explain_the_next_step(self, _load_dotenv: Mock) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ModelConfigurationError, "DATA_API_KEY"):
                create_structured_extractor()


if __name__ == "__main__":
    unittest.main()
