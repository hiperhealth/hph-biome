# AI Contributor Guide: hphbiome

This file is the shared operating manual for AI contributors working in the
`hph-biome` repository.

## Project Snapshot

- Library package: `hphbiome`
- HiperHealth adapter package: `hphbiome-hiperhealth`
- HiperHealth channel alias: `hphbiome`
- Runtime: Python `>=3.10,<4`
- Packaging: `setuptools` with per-package `src` layouts
- Development environment: `conda/dev.yaml`

## Core Objectives

1. Keep reusable HPH Biome logic in `packages/hphbiome` without a HiperHealth
   dependency.
2. Keep HiperHealth-specific integration in `packages/hphbiome-hiperhealth` and
   `skills/hphbiome`.
3. Keep package metadata, CI, release, and tooling configuration aligned with
   the monorepo layout.
4. Make minimal, targeted infrastructure changes with clear intent.
5. Do not commit secrets, credentials, real PHI, or sensitive data.

## Repository Layout

- `packages/hphbiome/`: standalone reusable library package
- `packages/hphbiome-hiperhealth/`: HiperHealth skill adapter package
- `skills-channel.yaml`: HiperHealth skill channel metadata
- `skills/hphbiome/`: installable HiperHealth skill manifest and entry point
- `tests/`: pytest coverage for library, adapter, and manifests
- `conda/dev.yaml`: cross-platform development environment definition
- `.makim.yaml`: task runner definitions
- `.github/workflows/`: CI, docs, and release workflows
- `pyproject.toml`: workspace metadata and shared tool configuration

## Tooling And Commands

Environment setup:

```bash
conda env create -f conda/dev.yaml
conda activate hphbiome
python -m pip install -e ".[dev]"
python -m pip install -e packages/hphbiome
python -m pip install -e packages/hphbiome-hiperhealth
```

If using mamba:

```bash
mamba env create -f conda/dev.yaml
mamba activate hphbiome
python -m pip install -e ".[dev]"
python -m pip install -e packages/hphbiome
python -m pip install -e packages/hphbiome-hiperhealth
```

High-value commands:

```bash
# unit tests with coverage threshold from .makim.yaml
makim tests.unit

# CI-like local checks
makim tests.ci

# lint/pre-commit stack
makim tests.linter
pre-commit run --all-files --verbose

# targeted static checks
ruff check packages tests
ruff format packages tests
mypy packages/hphbiome/src packages/hphbiome-hiperhealth/src

# package build
makim package.build
```

## Contributor Workflow Expectations

1. Inspect local files before planning changes.
2. Make focused edits and avoid unrelated churn.
3. Add or update tests when behavior changes.
4. Run targeted checks first, then broader checks when feasible.
5. Report any checks that could not be run and why.
