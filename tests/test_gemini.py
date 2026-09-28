from types import SimpleNamespace

from ai.gemini import GeminiClient
from ai.schemas import GeneratedContentSchema


VALID_RESPONSE = {
    "topic": "Algebra",
    "difficulty": "medium",
    "problem": "Solve 3x = x^9",
    "solution_steps": [
        "Move all terms to one side",
        "Factor out x",
        "Solve the resulting equations",
    ],
    "voice_script": (
        "First, move everything to one side. "
        "Then factor out x."
    ),
    "animation_spec": {
        "actions": [
            {
                "action": "write",
                "expression": "3x = x^9",
            },
            {
                "action": "transform",
                "from": "3x = x^9",
                "to": "x(3-x^8)=0",
            },
        ]
    },
}


class FakeModels:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def generate_content(self, **kwargs):
        self.calls.append(kwargs)
        return self.response


class FakeClient:
    def __init__(self, response):
        self.models = FakeModels(response)


def test_gemini_client_accepts_parsed_response():
    parsed = GeneratedContentSchema.model_validate(
        VALID_RESPONSE
    )

    fake_response = SimpleNamespace(
        parsed=parsed,
        text=parsed.model_dump_json(
            by_alias=True
        ),
    )

    fake_client = FakeClient(fake_response)

    client = GeminiClient(
        api_key="test-key",
        model="test-model",
        client=fake_client,
    )

    result = client.generate(
        topic="algebra",
        difficulty="medium",
    )

    assert isinstance(
        result,
        GeneratedContentSchema,
    )

    assert result.topic == "Algebra"
    assert result.difficulty.value == "medium"


def test_gemini_client_falls_back_to_json_text():
    fake_response = SimpleNamespace(
        parsed=None,
        text=GeneratedContentSchema(
            **VALID_RESPONSE
        ).model_dump_json(
            by_alias=True
        ),
    )

    fake_client = FakeClient(fake_response)

    client = GeminiClient(
        api_key="test-key",
        client=fake_client,
    )

    result = client.generate(
        topic="algebra",
        difficulty="medium",
    )

    assert result.problem == "Solve 3x = x^9"


def test_gemini_client_sends_structured_output_config():
    fake_response = SimpleNamespace(
        parsed=GeneratedContentSchema(
            **VALID_RESPONSE
        ),
        text="unused",
    )

    fake_client = FakeClient(fake_response)

    client = GeminiClient(
        api_key="test-key",
        model="test-model",
        client=fake_client,
    )

    client.generate(
        topic="algebra",
        difficulty="medium",
        audience="advanced students",
        additional_requirements=(
            "Prefer exact symbolic solutions."
        ),
    )

    call = fake_client.models.calls[0]

    config = call["config"]

    assert (
        config.response_mime_type
        == "application/json"
    )

    assert (
        config.response_schema
        == GeneratedContentSchema
    )

    assert call["model"] == "test-model"
