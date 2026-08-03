# hphbiome

Reusable HPH Biome library utilities.

This package is intentionally independent from HiperHealth so it can be used by
other Python projects. The HiperHealth skill adapter lives in the sibling
`hphbiome-hiperhealth` package.

## Usage

The example below uses fictional, non-sensitive data:

```python
from hphbiome import (
    build_biome_context,
    build_prompt_fragment,
    missing_recommended_fields,
)

patient = {
    'symptoms': 'Example symptom description',
    'dietary_history': 'Example dietary pattern',
    'stool_pattern': '',
}

missing_fields = missing_recommended_fields(patient)
context = build_biome_context(patient)
prompt_fragment = build_prompt_fragment()

print(missing_fields)
print(context)
print(prompt_fragment)
```

`missing_recommended_fields` identifies recommended fields without a value.
`build_biome_context` separates available fields from missing ones, and
`build_prompt_fragment` returns cautious guidance for downstream prompting.

These utilities organize supplied context only. They do not validate medical
claims, provide a diagnosis, recommend treatment, or replace professional
medical judgment.
