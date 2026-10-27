"""可编辑行程草案的离线测试。"""

from __future__ import annotations

import unittest
from datetime import date

from pydantic import ValidationError

from backend.travel_assistant.itinerary import (
    ItineraryDraftError,
    ItineraryStructuredOutputError,
    create_itinerary_draft,
)
from backend.travel_assistant.models import ClarificationPlan, ItineraryDraft, TravelRequest


class FakeGenerator:
    """离线替代模型，并记录是否收到调用。"""

    def __init__(self, result: object | Exception) -> None:
        self.result = result
        self.calls: list[dict[str, object]] = []

    def invoke(self, input_value: dict[str, object]) -> object:
        self.calls.append(input_value)
        if isinstance(self.result, Exception):
            raise self.result
        return self.result


def complete_request(days: int = 3) -> TravelRequest:
    """创建一份已通过校验的完整需求，供各测试复用。"""
    return TravelRequest(
        destination="杭州",
        start_date=date(2026, 11, 10),
        days=days,
        traveler_count=2,
        budget="5000 元",
        preferences=["自然风景", "慢节奏"],
        constraints=["行程不要太赶"],
    )


def suggestions(days: int = 3) -> dict[str, object]:
    """返回不含日期与确认承诺的模型建议。"""
    return {
        "daily_suggestions": [
            {
                "theme": f"第 {index} 天的慢节奏自然体验建议",
                "activities": [
                    {
                        "title": "自然风景散步建议",
                        "description": "建议根据体力和现场情况安排一段轻松的自然风景散步。",
                        "verification_status": "unverified",
                    }
                ],
            }
            for index in range(1, days + 1)
        ]
    }


class ItineraryDraftTests(unittest.TestCase):
    def test_complete_request_creates_three_continuous_draft_days(self) -> None:
        generator = FakeGenerator(suggestions())

        result = create_itinerary_draft(complete_request(), generator)

        self.assertIsInstance(result, ItineraryDraft)
        assert isinstance(result, ItineraryDraft)
        self.assertEqual(result.status, "draft")
        self.assertEqual(result.destination, "杭州")
        self.assertEqual(result.days, 3)
        self.assertEqual(
            [item.date for item in result.daily_items],
            [date(2026, 11, 10), date(2026, 11, 11), date(2026, 11, 12)],
        )
        self.assertEqual([item.day_number for item in result.daily_items], [1, 2, 3])
        self.assertTrue(all(activity.verification_status == "unverified" for item in result.daily_items for activity in item.activities))
        self.assertIn("未核实", " ".join(result.notes))
        self.assertEqual(generator.calls[0]["request_context"]["budget"], "5000 元")  # type: ignore[index]

    def test_single_day_trip_uses_start_date_as_end_date(self) -> None:
        generator = FakeGenerator(suggestions(days=1))

        result = create_itinerary_draft(complete_request(days=1), generator)

        self.assertIsInstance(result, ItineraryDraft)
        assert isinstance(result, ItineraryDraft)
        self.assertEqual(result.start_date, date(2026, 11, 10))
        self.assertEqual(result.end_date, date(2026, 11, 10))
        self.assertEqual(len(result.daily_items), 1)
        self.assertEqual(result.daily_items[0].date, date(2026, 11, 10))

    def test_incomplete_request_returns_clarification_without_calling_model(self) -> None:
        request = TravelRequest(destination="杭州", constraints=["父母同行"])
        generator = FakeGenerator(suggestions())

        result = create_itinerary_draft(request, generator)

        self.assertIsInstance(result, ClarificationPlan)
        assert isinstance(result, ClarificationPlan)
        self.assertEqual(result.missing_fields, ["start_date", "days", "traveler_count", "budget"])
        self.assertEqual(generator.calls, [])

    def test_rejects_wrong_number_of_model_days_without_partial_draft(self) -> None:
        generator = FakeGenerator(suggestions(days=2))

        with self.assertRaisesRegex(ItineraryStructuredOutputError, "数量与旅行天数不一致"):
            create_itinerary_draft(complete_request(), generator)

    def test_rejects_confirmation_or_booking_claims(self) -> None:
        invalid_suggestions = suggestions()
        first_activity = invalid_suggestions["daily_suggestions"][0]["activities"][0]  # type: ignore[index]
        first_activity["description"] = "该活动已经确认并已预订。"  # type: ignore[index]
        generator = FakeGenerator(invalid_suggestions)

        with self.assertRaisesRegex(ItineraryStructuredOutputError, "Pydantic 校验"):
            create_itinerary_draft(complete_request(), generator)

    def test_rejects_unverified_exact_price(self) -> None:
        invalid_suggestions = suggestions()
        first_activity = invalid_suggestions["daily_suggestions"][0]["activities"][0]  # type: ignore[index]
        first_activity["description"] = "建议购买 100 元门票后参观。"  # type: ignore[index]
        generator = FakeGenerator(invalid_suggestions)

        with self.assertRaisesRegex(ItineraryStructuredOutputError, "Pydantic 校验"):
            create_itinerary_draft(complete_request(), generator)

    def test_draft_model_rejects_noncontinuous_dates_and_non_draft_status(self) -> None:
        with self.assertRaisesRegex(ValidationError, "每日草案编号或日期"):
            ItineraryDraft(
                destination="杭州",
                start_date=date(2026, 11, 10),
                end_date=date(2026, 11, 12),
                days=3,
                traveler_count=2,
                budget="5000 元",
                daily_items=[
                    {"day_number": 1, "date": "2026-11-10", "theme": "建议", "activities": [{"title": "建议", "description": "建议体验"}]},
                    {"day_number": 2, "date": "2026-11-12", "theme": "建议", "activities": [{"title": "建议", "description": "建议体验"}]},
                    {"day_number": 3, "date": "2026-11-12", "theme": "建议", "activities": [{"title": "建议", "description": "建议体验"}]},
                ],
                notes=["动态信息未核实。"],
            )
        with self.assertRaises(ValidationError):
            ItineraryDraft(
                status="confirmed",
                destination="杭州",
                start_date=date(2026, 11, 10),
                end_date=date(2026, 11, 10),
                days=1,
                traveler_count=2,
                budget="5000 元",
                daily_items=[{"day_number": 1, "date": "2026-11-10", "theme": "建议", "activities": [{"title": "建议", "description": "建议体验"}]}],
                notes=["动态信息未核实。"],
            )

    def test_rejects_tampered_request_before_calling_model(self) -> None:
        request = complete_request()
        request.budget = None
        generator = FakeGenerator(suggestions())

        with self.assertRaisesRegex(ItineraryDraftError, "输入不一致"):
            create_itinerary_draft(request, generator)
        self.assertEqual(generator.calls, [])


if __name__ == "__main__":
    unittest.main()
