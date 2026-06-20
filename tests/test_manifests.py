from pathlib import Path

import pytest

yaml = pytest.importorskip('yaml')


ROOT = Path(__file__).resolve().parents[1]


def test_channel_manifest_declares_hphbiome_skill() -> None:
    manifest = yaml.safe_load((ROOT / 'skills-channel.yaml').read_text())

    assert manifest['api_version'] == 1
    assert manifest['channel']['default_alias'] == 'hphbiome'
    assert manifest['skills'] == [
        {
            'name': 'hphbiome',
            'enabled': True,
            'tags': ['microbiome', 'diagnosis', 'treatment'],
        }
    ]


def test_skill_manifest_matches_expected_channel_layout() -> None:
    manifest_path = ROOT / 'skills' / 'hphbiome' / 'skill.yaml'
    manifest = yaml.safe_load(manifest_path.read_text())

    assert manifest['name'] == 'hphbiome'
    assert manifest['entry_point'] == 'skill:HPHBiomeSkill'
    assert manifest['stages'] == ['diagnosis', 'treatment']
    assert 'hphbiome-hiperhealth>=0.1.0' in manifest['dependencies']
    assert (manifest_path.parent / 'skill.py').is_file()
