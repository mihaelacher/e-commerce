from collections.abc import Sequence


def tool_selection_metrics(results: Sequence[dict]) -> dict:
    if not results:
        raise ValueError("At least one tool-selection result is required.")

    tool_correct = 0
    arguments_correct = 0
    argument_cases = 0
    case_correct = 0
    failures = []

    for result in results:
        expected_tool_calls = result["expected_tool_calls"]
        actual_tool_calls = result["actual_tool_calls"]
        expected_tools = sorted(call["name"] for call in expected_tool_calls)
        actual_tools = sorted(call["name"] for call in actual_tool_calls)
        is_tool_correct = actual_tools == expected_tools

        has_expected_arguments = any(
            call.get("arguments") or call.get("expected_query_terms")
            for call in expected_tool_calls
        )
        is_arguments_correct = True
        remaining_actual_calls = list(actual_tool_calls)

        for expected_call in expected_tool_calls:
            actual_call_index = next(
                (
                    index
                    for index, call in enumerate(remaining_actual_calls)
                    if call["name"] == expected_call["name"]
                ),
                None,
            )
            if actual_call_index is None:
                is_arguments_correct = False
                continue

            actual_call = remaining_actual_calls.pop(actual_call_index)
            expected_arguments = expected_call.get("arguments", {})
            actual_arguments = actual_call.get("arguments") or {}
            expected_query_terms = expected_call.get(
                "expected_query_terms",
                [],
            )
            actual_query = str(actual_arguments.get("query", "")).lower()

            if not all(
                actual_arguments.get(key) == value
                for key, value in expected_arguments.items()
            ):
                is_arguments_correct = False

            if expected_query_terms and not any(
                term.lower() in actual_query for term in expected_query_terms
            ):
                is_arguments_correct = False

        if remaining_actual_calls:
            is_tool_correct = False

        if is_tool_correct:
            tool_correct += 1

        if has_expected_arguments:
            argument_cases += 1
            if is_arguments_correct:
                arguments_correct += 1

        if is_tool_correct and is_arguments_correct:
            case_correct += 1
        else:
            failures.append(
                {
                    "message": result["message"],
                    "expected_tool_calls": expected_tool_calls,
                    "actual_tool_calls": actual_tool_calls,
                }
            )

    total = len(results)
    return {
        "cases": total,
        "tool_selection_accuracy": tool_correct / total,
        "argument_accuracy": (
            arguments_correct / argument_cases if argument_cases else 1.0
        ),
        "case_accuracy": case_correct / total,
        "failures": failures,
    }


def retrieval_metrics(
    results: Sequence[dict],
    *,
    k: int,
) -> dict:
    if not results:
        raise ValueError("At least one retrieval result is required.")
    if k < 1:
        raise ValueError("k must be greater than 0.")

    relevant_cases = 0
    total_precision = 0.0
    total_recall = 0.0
    total_reciprocal_rank = 0.0
    no_answer_cases = 0
    correct_no_answer_cases = 0
    failures = []

    for result in results:
        expected = set(result["expected"])
        retrieved = result["retrieved"][:k]

        if expected:
            relevant_cases += 1
            hits = expected.intersection(retrieved)
            total_precision += len(hits) / k
            recall = len(hits) / len(expected)
            rank = next(
                (
                    index
                    for index, name in enumerate(retrieved, start=1)
                    if name in expected
                ),
                None,
            )
            total_recall += recall
            total_reciprocal_rank += 1 / rank if rank else 0.0

            if recall < 1:
                failures.append(
                    {
                        "query": result["query"],
                        "expected": sorted(expected),
                        "retrieved": retrieved,
                    }
                )
        else:
            no_answer_cases += 1
            if not retrieved:
                correct_no_answer_cases += 1
            else:
                failures.append(
                    {
                        "query": result["query"],
                        "expected": [],
                        "retrieved": retrieved,
                    }
                )

    return {
        "cases": len(results),
        "precision_at_k": (total_precision / relevant_cases if relevant_cases else 1.0),
        "recall_at_k": (total_recall / relevant_cases if relevant_cases else 1.0),
        "mrr_at_k": (total_reciprocal_rank / relevant_cases if relevant_cases else 1.0),
        "no_answer_accuracy": (
            correct_no_answer_cases / no_answer_cases if no_answer_cases else None
        ),
        "failures": failures,
    }
