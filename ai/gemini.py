from __future__ import annotations

import os

from google import genai
from google.genai import types

from ai.prompts import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from ai.schemas import GeneratedContentSchema


class GeminiError(Exception):
    """Base exception for Gemini failures."""


class GeminiConfigurationError(GeminiError):
    """Raised when Gemini configuration is missing or invalid."""


class GeminiGenerationError(GeminiError):
    """Raised when Gemini fails to generate valid content."""


class GeminiClient:
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        client=None,
    ):
        self.api_key = (
            api_key
            or os.getenv("GEMINI_API_KEY")
        )

        if not self.api_key and client is None:
            raise GeminiConfigurationError(
                "GEMINI_API_KEY is not configured."
            )

        self.model = (
            model
            or os.getenv(
                "GEMINI_MODEL",
                "gemini-2.5-flash",
            )
        )

        self.client = client or genai.Client(
            api_key=self.api_key
        )

    def generate(
        self,
        *,
        topic: str,
        difficulty: str,
        audience: str = "general mathematics audience",
        additional_requirements: str = "",
    ) -> GeneratedContentSchema:

        user_prompt = USER_PROMPT_TEMPLATE.format(
            topic=topic,
            difficulty=difficulty,
            audience=audience,
            additional_requirements=(
                additional_requirements
                or "None."
            ),
        )

        try:
            response = self.client.models.generate_content(
                model=self.model,
                contents=[
                    types.Content(
                        role="user",
                        parts=[
                            types.Part.from_text(
                                text=user_prompt
                            )
                        ],
                    )
                ],
                config=types.GenerateContentConfig(
                    system_instruction=SYSTEM_PROMPT,
                    response_mime_type="application/json",
                    response_schema=GeneratedContentSchema,
                ),
            )

        except Exception as exc:
            raise GeminiGenerationError(
                f"Gemini API request failed: {exc}"
            ) from exc

        try:
            parsed = getattr(
                response,
                "parsed",
                None,
            )

            if parsed is not None:
                if isinstance(
                    parsed,
                    GeneratedContentSchema,
                ):
                    return parsed

                return GeneratedContentSchema.model_validate(
                    parsed
                )

            response_text = getattr(
                response,
                "text",
                None,
            )

            if not response_text:
                raise GeminiGenerationError(
                    "Gemini returned an empty response."
                )

            return GeneratedContentSchema.model_validate_json(
                response_text
            )

        except GeminiGenerationError:
            raise

        except Exception as exc:
            raise GeminiGenerationError(
                "Gemini returned data that does not "
                "match the required content schema."
            ) from exc
