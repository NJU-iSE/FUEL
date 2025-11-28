# Prompt: Analyze Bug (Oracle Violation)

## Context

The {{lib}} model violated the oracle during execution. This is likely a potential framework bug where different backends produce inconsistent results.

{{examples}}

---

## Current Test Case

### {{lib}} Model Definition

```python
{{code}}
```

### Bug Symptom

{{bug}}

---

## Task

Analyze whether this is a potential bug in {{lib}}. This model passed validation but produced different results or behaviors between backends.

Help me summarize the bug symptoms in three short sentences following this format:

### Result Analysis

1. **Explanation**: [Confirm this is a potential bug and describe the symptom]
2. **Reasons**: [Root cause analysis - why this oracle violation occurred]
3. **Next Testing Strategy**: [How to trigger more similar bugs with related operators or patterns]

