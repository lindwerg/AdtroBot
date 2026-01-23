---
phase: quick
plan: 001
type: execute
wave: 1
depends_on: []
files_modified:
  - src/services/ai/validators.py
  - src/services/ai/client.py
autonomous: true

must_haves:
  truths:
    - "Natal chart interpretation passes validation"
    - "Validation checks for NatalChartPrompt sections (emoji headers)"
    - "User sees natal interpretation instead of error"
  artifacts:
    - path: "src/services/ai/validators.py"
      provides: "NatalChartOutput validator and validate_natal_chart function"
      contains: "class NatalChartOutput"
    - path: "src/services/ai/client.py"
      provides: "Updated generate_natal_interpretation using validate_natal_chart"
      contains: "validate_natal_chart"
  key_links:
    - from: "src/services/ai/client.py"
      to: "src/services/ai/validators.py"
      via: "import validate_natal_chart"
      pattern: "from src.services.ai.validators import.*validate_natal_chart"
---

<objective>
Fix natal chart validation to match actual NatalChartPrompt output sections.

**Problem:**
- `generate_natal_interpretation()` uses `validate_horoscope()` which checks for ["любовь", "карьер", "здоровь", "финанс"]
- `NatalChartPrompt` generates sections: 🌟 БОЛЬШАЯ ТРОЙКА, 💫 ЛИЧНОСТЬ, 🎯 ПУТЬ РАЗВИТИЯ, ⚡ КЛЮЧЕВЫЕ АСПЕКТЫ, 💎 ИТОГ
- Result: All natal interpretations fail with "Отсутствуют разделы гороскопа (найдено 0/4)"

**Solution:**
Create `NatalChartOutput` validator with correct section keywords and use it in `generate_natal_interpretation()`.

Purpose: Users can receive natal chart interpretations instead of error messages.
Output: Working natal chart validation and interpretation flow.
</objective>

<execution_context>
@~/.claude/get-shit-done/workflows/execute-plan.md
@~/.claude/get-shit-done/templates/summary.md
</execution_context>

<context>
@src/services/ai/validators.py
@src/services/ai/client.py
@src/services/ai/prompts.py (NatalChartPrompt class)
</context>

<tasks>

<task type="auto">
  <name>Task 1: Add NatalChartOutput validator to validators.py</name>
  <files>src/services/ai/validators.py</files>
  <action>
Add new Pydantic model `NatalChartOutput` and function `validate_natal_chart()`:

1. Create `NatalChartOutput(BaseModel)` with:
   - text: str field
   - @field_validator("text") that checks:
     - Minimum length: 800 chars (400-500 words in Russian)
     - Maximum length: 3000 chars
     - Required section keywords (at least 3 of 5):
       - "большая тройка" (case-insensitive)
       - "личность"
       - "путь развития" OR "развити"
       - "ключевые аспекты" OR "аспект"
       - "итог"
     - No forbidden AI patterns (reuse `_check_forbidden_patterns`)

2. Add `validate_natal_chart(text: str) -> tuple[bool, str | None]` function:
   - Same pattern as `validate_horoscope`, `validate_tarot`
   - Returns (True, None) if valid
   - Returns (False, error_message) if invalid
  </action>
  <verify>
Run: `python -c "from src.services.ai.validators import validate_natal_chart, NatalChartOutput; print('Import OK')"`
  </verify>
  <done>
`NatalChartOutput` class exists with section validation for natal chart sections.
`validate_natal_chart()` function exported and callable.
  </done>
</task>

<task type="auto">
  <name>Task 2: Update client.py to use validate_natal_chart</name>
  <files>src/services/ai/client.py</files>
  <action>
1. Update import (line 25):
   ```python
   from src.services.ai.validators import validate_card_of_day, validate_horoscope, validate_tarot, validate_natal_chart
   ```

2. Update `generate_natal_interpretation()` method (line 389):
   Replace:
   ```python
   is_valid, error = validate_horoscope(text)
   ```
   With:
   ```python
   is_valid, error = validate_natal_chart(text)
   ```

3. Keep all other code unchanged (caching, retries, logging).
  </action>
  <verify>
Run: `python -c "from src.services.ai.client import AIService; print('Import OK')"`
Run: `grep -n "validate_natal_chart" src/services/ai/client.py`
  </verify>
  <done>
`generate_natal_interpretation()` uses `validate_natal_chart()` instead of `validate_horoscope()`.
Import statement updated.
  </done>
</task>

<task type="auto">
  <name>Task 3: Verify fix with unit test</name>
  <files>tests/services/ai/test_validators.py</files>
  <action>
Add test for `validate_natal_chart()` in test_validators.py (or create file if doesn't exist):

```python
def test_validate_natal_chart_valid():
    """Test natal chart validation with proper sections."""
    valid_text = """
🌟 БОЛЬШАЯ ТРОЙКА
Твоё Солнце в Овне дает тебе энергию первопроходца. Луна в Раке делает тебя эмоционально чувствительным.
Асцендент в Льве придает харизму и уверенность в себе.

💫 ЛИЧНОСТЬ
Меркурий в Овне делает твой ум быстрым и решительным. Венера в Рыбах дарит романтичность и мечтательность.
Марс в Козероге направляет энергию на достижение целей.

🎯 ПУТЬ РАЗВИТИЯ
Юпитер в Тельце расширяет возможности в материальной сфере. Сатурн в Водолее учит дисциплине в социуме.

⚡ КЛЮЧЕВЫЕ АСПЕКТЫ
Солнце в трине с Юпитером - природный оптимизм и везение. Луна в квадрате с Сатурном - эмоциональные уроки.

💎 ИТОГ
Твоя сильная сторона - решительность и способность вести за собой. Рекомендация: развивай эмоциональный интеллект.
""".strip()

    is_valid, error = validate_natal_chart(valid_text)
    assert is_valid is True
    assert error is None


def test_validate_natal_chart_invalid_sections():
    """Test natal chart validation fails with wrong sections."""
    invalid_text = """
[ЛЮБОВЬ]
Сегодня хороший день для романтики.

[КАРЬЕРА]
На работе все будет отлично.
"""

    is_valid, error = validate_natal_chart(invalid_text)
    assert is_valid is False
    assert "разделы" in error.lower() or "секции" in error.lower() or "найдено" in error.lower()
```

Run tests to verify both pass.
  </action>
  <verify>
Run: `pytest tests/services/ai/test_validators.py -v -k "natal_chart" --no-header`
  </verify>
  <done>
Tests pass for both valid natal chart text and invalid (horoscope-style) text.
  </done>
</task>

</tasks>

<verification>
1. `python -c "from src.services.ai.validators import validate_natal_chart; print('OK')"` - import works
2. `python -c "from src.services.ai.client import AIService; print('OK')"` - client imports updated validator
3. `grep "validate_natal_chart" src/services/ai/client.py` - shows usage in generate_natal_interpretation
4. `pytest tests/services/ai/test_validators.py -v -k "natal"` - tests pass
</verification>

<success_criteria>
- NatalChartOutput validates sections: БОЛЬШАЯ ТРОЙКА, ЛИЧНОСТЬ, ПУТЬ РАЗВИТИЯ, КЛЮЧЕВЫЕ АСПЕКТЫ, ИТОГ
- generate_natal_interpretation() uses validate_natal_chart() instead of validate_horoscope()
- Tests confirm valid natal output passes, invalid (horoscope-style) output fails
- No regressions in existing validators (validate_horoscope, validate_tarot, validate_card_of_day)
</success_criteria>

<output>
After completion, create `.planning/quick/001-create-natalchartoutput-validator-and-us/001-SUMMARY.md`
</output>
