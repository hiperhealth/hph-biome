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


def test_issue_templates_have_valid_yaml_and_community_links() -> None:
    templates = ROOT / '.github' / 'ISSUE_TEMPLATE'
    code_of_conduct = ROOT / 'CODE_OF_CONDUCT.md'

    for template in templates.glob('*.yml'):
        text = template.read_text(encoding='utf-8')
        documents = list(yaml.safe_load_all(text))

        assert documents
        assert isinstance(documents[0], dict)
        if 'github.com/hiperhealth/hph-biome' in text:
            assert (
                'CODE_OF_CONDUCT.md' not in text or code_of_conduct.is_file()
            )
