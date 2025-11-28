# Prompt: Analyze Coverage Results

## Context

The {{lib}} model executed successfully. Analyze the code coverage result to understand whether new code paths were triggered.

{{examples}}

---

## Current Test Case

### {{lib}} Model Definition

```python
{{code}}
```

### Coverage Result

{{coverage}}

---

## Task

Please analyze the coverage result of this {{lib}} code which executes on Eager and Compiler backends.

Help me summarize the coverage result in three short sentences following this format:

### Result Analysis

1. **Explanation**: [Brief summary - did this model trigger new coverage?]
2. **Reasons**: [Root cause analysis - why did/didn't it trigger new coverage?]
3. **Next Testing Strategy**: [Concrete suggestions for improving coverage]

