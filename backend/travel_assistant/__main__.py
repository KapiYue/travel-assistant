"""Command-line entry point for observing travel-request extraction."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from backend.travel_assistant.extraction import (
    EmptyTravelRequestError,
    ModelConfigurationError,
    ModelInvocationError,
    StructuredOutputValidationError,
    extract_travel_request,
)
from backend.travel_assistant.clarification import (
    ClarificationPlanError,
    create_clarification_plan,
)


def main(argv: Sequence[str] | None = None) -> int:
    """Run one extraction and print its validated JSON representation."""
    parser = argparse.ArgumentParser(description="从自然语言中提取经过校验的旅行需求。")
    parser.add_argument("description", nargs="*", help="旅行需求，例如：两个人 2026 年 11 月去杭州玩 3 天")
    arguments = parser.parse_args(argv)
    user_input = " ".join(arguments.description)

    if not user_input:
        try:
            user_input = input("请输入旅行需求：")
        except EOFError:
            user_input = ""

    try:
        request = extract_travel_request(user_input)
    except EmptyTravelRequestError as error:
        print(error)
        return 2
    except ModelConfigurationError as error:
        print(error)
        return 3
    except ModelInvocationError as error:
        print(error)
        return 4
    except StructuredOutputValidationError as error:
        print(error)
        return 5

    try:
        plan = create_clarification_plan(request)
    except ClarificationPlanError as error:
        print(error)
        return 6

    print(
        json.dumps(
            {
                "travel_request": request.model_dump(mode="json"),
                "clarification_plan": plan.model_dump(mode="json"),
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
