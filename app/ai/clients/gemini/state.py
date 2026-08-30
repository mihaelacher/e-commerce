from google.genai import types


def serialize_state(
    state: list[types.Content],
) -> list[dict]:
    return [
        content.model_dump(
            mode="json",
            exclude_none=True,
        )
        for content in state
    ]


def deserialize_state(
    state: list[dict],
) -> list[types.Content]:
    return [
        types.Content.model_validate(content)
        for content in state
    ]