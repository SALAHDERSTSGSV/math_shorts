from __future__ import annotations

from domain.artifacts import (
    AnimationSpec as DomainAnimationSpec,
    Difficulty,
    GeneratedContent,
)

from ai.schemas import GeneratedContentSchema


def to_domain_content(
    content: GeneratedContentSchema,
) -> GeneratedContent:

    animation_spec = content.animation_spec

    domain_animation = DomainAnimationSpec(
        objects=tuple(
            obj.model_dump(
                by_alias=True,
                exclude_none=True,
            )
            for obj in animation_spec.objects
        ),
        animations=tuple(
            animation.model_dump(
                by_alias=True,
                exclude_none=True,
            )
            for animation in animation_spec.animations
        ),
        actions=tuple(
            action.model_dump(
                by_alias=True,
                exclude_none=True,
            )
            for action in animation_spec.actions
        ),
    )

    return GeneratedContent(
        topic=content.topic,
        difficulty=Difficulty(
            content.difficulty.value
        ),
        problem=content.problem,
        solution_steps=tuple(
            content.solution_steps
        ),
        voice_script=content.voice_script,
        animation_spec={
            "objects": list(
                domain_animation.objects
            ),
            "animations": list(
                domain_animation.animations
            ),
            "actions": list(
                domain_animation.actions
            ),
        },
    )
