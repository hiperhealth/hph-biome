from __future__ import annotations

import importlib
import sys
import types

from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class FakeStage(str, Enum):
    DIAGNOSIS = 'diagnosis'
    TREATMENT = 'treatment'
    SCREENING = 'screening'


@dataclass(frozen=True)
class FakeSkillMetadata:
    name: str
    version: str = '0.1.0'
    stages: tuple[str, ...] = ()
    description: str = ''


@dataclass
class FakeInquiry:
    skill_name: str
    stage: str
    field: str
    label: str
    description: str = ''
    priority: str = 'supplementary'
    input_type: str = 'text'
    choices: list[str] | None = None


class FakeBaseSkill:
    def __init__(self, metadata: FakeSkillMetadata) -> None:
        self.metadata = metadata


@dataclass
class FakePipelineContext:
    patient: dict[str, Any] = field(default_factory=dict)
    results: dict[str, Any] = field(default_factory=dict)
    extras: dict[str, Any] = field(default_factory=dict)
    session_id: str | None = None


def install_fake_hiperhealth() -> None:
    pipeline = types.ModuleType('hiperhealth.pipeline')
    pipeline.BaseSkill = FakeBaseSkill
    pipeline.Inquiry = FakeInquiry
    pipeline.SkillMetadata = FakeSkillMetadata
    pipeline.Stage = FakeStage

    context = types.ModuleType('hiperhealth.pipeline.context')
    context.PipelineContext = FakePipelineContext

    hiperhealth = types.ModuleType('hiperhealth')
    hiperhealth.pipeline = pipeline

    sys.modules['hiperhealth'] = hiperhealth
    sys.modules['hiperhealth.pipeline'] = pipeline
    sys.modules['hiperhealth.pipeline.context'] = context


def import_skill_module() -> types.ModuleType:
    install_fake_hiperhealth()
    sys.modules.pop('hphbiome_hiperhealth', None)
    sys.modules.pop('hphbiome_hiperhealth.skill', None)
    return importlib.import_module('hphbiome_hiperhealth.skill')


def test_skill_metadata_and_requirement_inquiries() -> None:
    module = import_skill_module()
    skill = module.HPHBiomeSkill()
    ctx = FakePipelineContext(patient={'symptoms': 'bloating'})

    inquiries = skill.check_requirements(FakeStage.DIAGNOSIS, ctx)

    assert skill.metadata.name == 'hphbiome'
    assert FakeStage.DIAGNOSIS in skill.metadata.stages
    assert {inquiry.field for inquiry in inquiries} >= {
        'dietary_history',
        'stool_pattern',
    }
    assert all(inquiry.priority == 'supplementary' for inquiry in inquiries)
    assert skill.check_requirements(FakeStage.TREATMENT, ctx) == []


def test_skill_injects_prompt_fragments_and_results() -> None:
    module = import_skill_module()
    skill = module.HPHBiomeSkill()
    ctx = FakePipelineContext(patient={'symptoms': 'bloating'})

    ctx = skill.pre(FakeStage.DIAGNOSIS, ctx)
    ctx = skill.execute(FakeStage.DIAGNOSIS, ctx)

    assert 'clinician judgment' in ctx.extras['prompt_fragments']['diagnosis']
    assert 'diet' in ctx.extras['prompt_fragments']['diagnosis_requirements']
    assert ctx.results['diagnosis']['hphbiome']['available_fields'] == {
        'symptoms': 'bloating'
    }


def test_package_lazy_exports_skill_and_version_fallback(monkeypatch) -> None:
    install_fake_hiperhealth()
    sys.modules.pop('hphbiome_hiperhealth', None)
    package = importlib.import_module('hphbiome_hiperhealth')

    def raise_not_found(_: str) -> str:
        raise package.PackageNotFoundError

    monkeypatch.setattr(package, 'version', raise_not_found)

    assert package.HPHBiomeSkill.__name__ == 'HPHBiomeSkill'
    assert package._version() == '0.1.0'

    try:
        package.not_available
    except AttributeError as exc:
        assert str(exc) == 'not_available'
    else:
        raise AssertionError('Expected AttributeError')


def test_skill_ignores_unregistered_stage_and_appends_fragment() -> None:
    module = import_skill_module()
    skill = module.HPHBiomeSkill()
    ctx = FakePipelineContext(
        patient={'symptoms': 'bloating'},
        extras={'prompt_fragments': {'treatment': 'Existing fragment.'}},
    )

    unchanged = skill.pre(FakeStage.SCREENING, ctx)
    unchanged = skill.execute(FakeStage.SCREENING, unchanged)
    changed = skill.pre(FakeStage.TREATMENT, unchanged)
    changed = skill.execute(FakeStage.TREATMENT, changed)

    assert changed.extras['prompt_fragments']['treatment'].startswith(
        'Existing fragment.\n\nConsider gut microbiome'
    )
    assert 'screening' not in changed.results
    assert 'hphbiome' in changed.results['treatment']
