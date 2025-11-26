# Bug vs Exception 分离 - 实现总结

## 🎯 目标

将**框架bug**（Oracle违反）和**无效测试**（代码错误）明确区分开，使fuzzing系统能够：
1. 针对bug提供更精准的分析和复现策略
2. 针对无效测试提供修复建议
3. 提高LLM分析的准确性

## 📊 分类标准

### Bug (Oracle Violation)
- **特征**: 代码在某个backend通过，但在另一个backend失败或产生不一致结果
- **例如**: 
  - Eager mode成功，Inductor失败
  - 两个backend结果数值不一致（INCON）
  - CPU成功，CUDA失败
- **Oracle类型**: `TARGET_EXCEPTION`, `INCON`, `MISALIGN`
- **写入**: `bug_report.log`

### Exception (Invalid Test)
- **特征**: 代码在所有backend都失败
- **例如**:
  - 语法错误
  - 类型不匹配
  - Tensor shape不兼容
  - 参数范围错误
- **Oracle类型**: `BASE_EXCEPTION`, `TRANSFER_EXCEPTION`
- **不写入**: bug_report.log

## 🔄 实现的改动

### 1. **Examples 重命名**

```
prompts/als/examples/
├── bug_example1/          # 原exception_example1（Oracle violation）
│   ├── code.md
│   ├── bug.md            # 原exception.md
│   └── analysis.md
├── bug_example2/          # 原exception_example3（Oracle violation）
│   ├── code.md
│   ├── bug.md
│   └── analysis.md
├── exception_example1/    # 原exception_example2（Invalid test）
│   ├── code.md
│   ├── exception.md
│   └── analysis.md
└── ...
```

### 2. **新的 Prompt 模板**

#### `prompts/als/failure_bug.md`
```markdown
# Prompt: Analyze Bug (Oracle Violation)

用于分析违反oracle的情况，重点关注：
- 确认是框架bug
- 分析root cause
- 提供触发similar bugs的策略
```

#### `prompts/als/failure_exception.md` (更新)
```markdown
# Prompt: Analyze Exception (Invalid Test Case)

用于分析无效测试，重点关注：
- 确认是代码问题
- 分析错误原因
- 提供修复建议
```

### 3. **代码修改**

#### `fuel/utils/prompt_loader.py`
- 添加 `bug` 字段到 `Example` 类
- `format_examples()` 支持 `include_bug` 参数
- `load_als_prompts()` 加载 bug 和 exception 两种模板

#### `fuel/utils/prompt_handler.py`
- `get_prompts()` 根据 `FeedBack.has_bug` 选择prompt:
  - `has_bug=True` → 使用 bug analysis prompt
  - `has_bug=False` → 使用 exception analysis prompt

#### `fuel/utils/fuzzing_core.py`
- `process_feedback()` 区分两种feedback:
  - Bug: `{"code": ..., "bug": ...}`
  - Exception: `{"code": ..., "exception": ...}`
- 在feedback日志中标记 `[BUG]` 或 `[EXCEPTION]`

### 4. **判断逻辑流程**

```
执行测试
    ↓
DiffTesting
    ↓
检查结果
    ├─→ 两个backend都成功且结果一致
    │   └→ statue=True, has_bug=False
    │
    ├─→ 一个backend成功，另一个失败
    │   └→ statue=False, has_bug=True
    │       └→ 写入bug_report.log
    │       └→ 使用bug analysis prompt
    │
    ├─→ 两个backend都成功但结果不一致
    │   └→ statue=False, has_bug=True
    │       └→ 写入bug_report.log
    │       └→ 使用bug analysis prompt
    │
    └─→ 两个backend都失败
        └→ statue=False, has_bug=False
            └→ 不写入bug_report.log
            └→ 使用exception analysis prompt
```

## 📈 效果

### Before
- 所有失败都用同一个prompt分析
- LLM需要自己判断是bug还是invalid test
- 分析不够精准，策略混乱

### After
- Bug和exception分开处理
- 针对性的prompt提供更精确的分析
- Bug: 关注复现和触发similar bugs
- Exception: 关注修复和避免类似错误

## 🔍 验证方式

### 1. 检查Examples分类
```bash
# Bug examples (oracle violations)
ls prompts/als/examples/bug_example*/

# Exception examples (invalid tests)
ls prompts/als/examples/exception_example*/
```

### 2. 检查Prompt内容
```bash
# Bug prompt - 应该关注"potential bug"和"trigger similar bugs"
cat prompts/als/failure_bug.md

# Exception prompt - 应该关注"invalid model"和"how to fix"
cat prompts/als/failure_exception.md
```

### 3. 运行Fuzzing
```bash
python -m fuel.fuzz --lib pytorch run_fuzz --max_round 10
```

检查日志中是否正确标记：
- `output/pytorch/feedback.log` 中应该有 `[BUG]` 或 `[EXCEPTION]` 标记
- `output/pytorch/bug_report.log` 应该只包含oracle violations

## 💡 使用建议

1. **添加新的bug examples**: 将真实发现的oracle violations添加到 `bug_example_N/`
2. **添加新的exception examples**: 将常见的无效模式添加到 `exception_example_N/`
3. **调整prompt**: 根据实际效果优化 `failure_bug.md` 和 `failure_exception.md`
4. **监控分类准确性**: 定期检查bug_report.log，确保没有误报

## 🔗 相关文件

- `fuel/utils/prompt_loader.py` - Prompt加载器
- `fuel/utils/prompt_handler.py` - Prompt处理器
- `fuel/utils/fuzzing_core.py` - Fuzzing核心逻辑
- `fuel/feedback/feedback.py` - FeedBack类定义
- `fuel/exec/exec_template.py` - Oracle判断逻辑
- `prompts/als/failure_bug.md` - Bug分析prompt模板
- `prompts/als/failure_exception.md` - Exception分析prompt模板

