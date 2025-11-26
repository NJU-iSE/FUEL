# Prompt: Analyze Exception Results

## Context

The {{lib}} model encountered an exception during execution. Analyze whether this is a framework bug or an invalid model.

{{examples}}

---

## Current Test Case

### {{lib}} Model Definition

```python
{{code}}
```

### Bug Symptom

{{exception}}

---

## Task

Analyze whether this is an invalid model caused by the code itself or a potential bug in {{lib}}.

Help me summarize the symptoms in three short sentences following this format:

### Result Analysis

1. **Explanation**: [Is this a potential bug or an invalid model?]
2. **Reasons**: [Root cause analysis - what caused this issue?]
3. **Next Testing Strategy**: [If invalid model: how to fix it? If bug: how to trigger similar bugs?]

