from __future__ import annotations

from typing import Any

from hiperhealth.pipeline import BaseSkill, Inquiry, SkillMetadata, Stage
from hiperhealth.pipeline.context import PipelineContext

from hphbiome import (
    __version__ as hphbiome_version,
)
from hphbiome import (
    build_biome_context,
    build_prompt_fragment,
    field_description,
    field_label,
    missing_recommended_fields,
)

DIAGNOSIS_STAGE = 'diagnosis'
TREATMENT_STAGE = 'treatment'


def _stage_value(stage: str | Stage) -> str:
    value = getattr(stage, 'value', stage)
    return str(value)


class HPHBiomeSkill(BaseSkill):
    def __init__(self) -> None:
        super().__init__(
            SkillMetadata(
                name='hphbiome',
                version=hphbiome_version,
                stages=(Stage.DIAGNOSIS, Stage.TREATMENT),
                description=(
                    'Adds gut microbiome context to diagnosis and treatment '
                    'stages.'
                ),
            )
        )

    def check_requirements(
        self,
        stage: str | Stage,
        ctx: PipelineContext,
    ) -> list[Inquiry]:
        if _stage_value(stage) != DIAGNOSIS_STAGE:
            return []

        return [
            Inquiry(
                skill_name=self.metadata.name,
                stage=_stage_value(stage),
                field=field,
                label=field_label(field),
                description=field_description(field),
                priority='supplementary',
                input_type='text',
                choices=None,
            )
            for field in missing_recommended_fields(ctx.patient)
        ]

    def pre(
        self,
        stage: str | Stage,
        ctx: PipelineContext,
    ) -> PipelineContext:
        stage_key = _stage_value(stage)
        if stage_key not in {DIAGNOSIS_STAGE, TREATMENT_STAGE}:
            return ctx

        fragments = ctx.extras.setdefault('prompt_fragments', {})
        fragment = build_prompt_fragment()
        fragments[stage_key] = _append_fragment(
            fragments.get(stage_key),
            fragment,
        )

        if stage_key == DIAGNOSIS_STAGE:
            requirement_key = f'{stage_key}_requirements'
            fragments[requirement_key] = _append_fragment(
                fragments.get(requirement_key),
                (
                    'For microbiome-aware assessment, consider whether diet, '
                    'stool pattern, recent antibiotics, medications, '
                    'allergies, and current symptoms are available.'
                ),
            )

        return ctx

    def execute(
        self,
        stage: str | Stage,
        ctx: PipelineContext,
    ) -> PipelineContext:
        stage_key = _stage_value(stage)
        if stage_key not in {DIAGNOSIS_STAGE, TREATMENT_STAGE}:
            return ctx

        stage_results = ctx.results.setdefault(stage_key, {})
        stage_results['hphbiome'] = build_biome_context(ctx.patient)
        return ctx


def _append_fragment(existing: Any, fragment: str) -> str:
    if not existing:
        return fragment
    return f'{existing}\n\n{fragment}'
