# hphbiome

HPH Biome is organized as a small monorepo with two Python packages:

- `hphbiome`: reusable library code with no HiperHealth dependency.
- `hphbiome-hiperhealth`: a thin HiperHealth skill adapter that consumes the
  library package.

The repository also exposes a HiperHealth skill channel through
`skills-channel.yaml` and the skill manifest in `skills/hphbiome/skill.yaml`.

## Development install

```bash
python -m pip install -e ".[dev]"
python -m pip install -e packages/hphbiome
python -m pip install -e packages/hphbiome-hiperhealth
```

## HiperHealth channel usage

After installing the HiperHealth host application, register this repository as a
local channel:

```python
from hiperhealth.pipeline import SkillRegistry

registry = SkillRegistry()
registry.add_channel('/path/to/hph-biome', local_name='hphbiome')
registry.install_skill('hphbiome.hphbiome')
```

The skill can also be discovered as a Python entry point from the
`hphbiome-hiperhealth` package.

For local development before the packages are published, install both packages
editably before installing the skill from the local channel.
