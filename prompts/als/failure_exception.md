# Prompt: Analyze Exception (Invalid Test Case)

## Context

The {{lib}} model encountered exceptions in both backends during execution. This indicates the test case itself is invalid (syntax error, type mismatch, shape incompatibility, etc.), not a framework bug.

{{examples}}

---

## Current Test Case

### {{lib}} Model Definition

```python
{{code}}
```

### Exception Message

{{exception}}

---

## Task

Analyze why this is an invalid model and how to fix it. The model failed in both backends, indicating it's a problem with the test case itself, not a framework bug.

Help me summarize the issue in three short sentences following this format:

### Result Analysis

1. **Explanation**: [Confirm this is an invalid model and identify the issue]
2. **Reasons**: [Root cause - what's wrong with the code?]
3. **Next Testing Strategy**: [How to fix this model to make it valid]

