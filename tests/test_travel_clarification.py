"""Offline tests for deterministic travel-request clarification planning."""

from __future__ import annotations

import unittest
from datetime import date
from unittest.mock import patch

from pydantic import ValidationError

from backend.travel_assistant.clarification import (
    ClarificationPlanError,
    create_clarification_plan,
)
from backend.travel_assistant.models import ClarificationPlan, TravelRequest


class ClarificationPlanTests(unittest.TestCase):
    def test_complete_request_needs_no_questions_or_model(self) -> None:
        request = TravelRequest(
            destination="杭州",
            start_date=date(2026, 11, 10),
            days=3,
            traveler_count=2,
            budget="5000 元",
            preferences=["自然风景"],
        )

        with patch("backend.travel_assistant.extraction.create_structured_extractor") as create_extractor:
            plan = create_clarification_plan(request)

        create_extractor.assert_not_called()

        self.assertEqual(plan.missing_fields, [])
        self.assertEqual(plan.questions, [])
        self.assertTrue(plan.is_complete)
        self.assertEqual(plan.message, "信息已齐全，可以进入后续阶段。")

    def test_only_missing_budget_creates_one_budget_question(self) -> None:
        request = TravelRequest(
            destination="杭州",
            start_date=date(2026, 11, 10),
            days=3,
            traveler_count=2,
        )

        plan = create_clarification_plan(request)

        self.assertEqual(plan.missing_fields, ["budget"])
        self.assertEqual([question.field for question in plan.questions], ["budget"])
        self.assertIn("预算", plan.questions[0].prompt)
        self.assertFalse(plan.is_complete)

    def test_parent_trip_does_not_infer_count_and_uses_stable_order(self) -> None:
        request = TravelRequest(
            destination="杭州",
            preferences=["自然风景"],
            constraints=["父母同行"],
        )

        plan = create_clarification_plan(request)

        self.assertEqual(
            plan.missing_fields,
            ["start_date", "days", "traveler_count", "budget"],
        )
        self.assertEqual(
            [question.field for question in plan.questions],
            ["start_date", "days", "traveler_count", "budget"],
        )
        self.assertNotIn("目的地", " ".join(question.prompt for question in plan.questions))
        self.assertNotIn("偏好", " ".join(question.prompt for question in plan.questions))

    def test_multiple_missing_fields_follow_workflow_order(self) -> None:
        request = TravelRequest(days=2)

        plan = create_clarification_plan(request)

        self.assertEqual(
            plan.missing_fields,
            ["destination", "start_date", "traveler_count", "budget"],
        )

    def test_inconsistent_missing_fields_fails_without_partial_plan(self) -> None:
        request = TravelRequest(destination="杭州")
        request.missing_fields = ["budget", "days"]

        with self.assertRaisesRegex(ClarificationPlanError, "输入不一致"):
            create_clarification_plan(request)

    def test_unknown_or_duplicate_rule_input_is_rejected(self) -> None:
        with self.assertRaisesRegex(ValueError, "未知缺失字段"):
            ClarificationPlan(missing_fields=["destination", "hotel"])
        with self.assertRaisesRegex(ValueError, "重复缺失字段"):
            ClarificationPlan(missing_fields=["budget", "budget"])

    def test_derived_plan_fields_cannot_be_supplied_by_caller(self) -> None:
        with self.assertRaisesRegex(ValueError, "必须由追问规则层计算"):
            ClarificationPlan(missing_fields=[], is_complete=False)

        plan = ClarificationPlan(missing_fields=[])
        with self.assertRaises(ValidationError):
            plan.is_complete = False

    def test_rejects_unvalidated_or_invalid_request_input(self) -> None:
        invalid_request = TravelRequest.model_construct(
            destination=None,
            start_date=None,
            end_date=None,
            days=0,
            traveler_count=None,
            budget=None,
            preferences=[],
            constraints=[],
            missing_fields=["destination", "start_date", "traveler_count", "budget"],
        )

        with self.assertRaisesRegex(ClarificationPlanError, "Pydantic 校验"):
            create_clarification_plan(invalid_request)
        with self.assertRaisesRegex(ClarificationPlanError, "只接受"):
            create_clarification_plan(object())  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
