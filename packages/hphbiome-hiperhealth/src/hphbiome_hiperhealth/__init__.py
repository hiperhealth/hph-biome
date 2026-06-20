from __future__ import annotations

from importlib.metadata import PackageNotFoundError, version
from typing import Any


def _version() -> str:
    try:
        return version('hphbiome-hiperhealth')
    except PackageNotFoundError:
        return '0.1.0'


def __getattr__(name: str) -> Any:
    if name == 'HPHBiomeSkill':
        from hphbiome_hiperhealth.skill import HPHBiomeSkill

        return HPHBiomeSkill
    raise AttributeError(name)


__version__ = _version()

__all__ = ['HPHBiomeSkill', '__version__']
