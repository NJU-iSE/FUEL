# FUEL Prompt Templates

This directory contains prompt templates for FUEL's LLM-based fuzzing system, inspired by [KNighter](https://github.com/seclab-ucr/KNighter)'s elegant prompt management approach.

## 📂 Directory Structure

```
prompts/
├── gen/                          # Generation prompts
│   ├── system.md                 # System prompt for code generation
│   ├── success.md               # Prompt after successful execution
│   ├── failure.md               # Prompt after failed execution
│   ├── default.md               # Default/initial prompt
│   ├── knowledge/               # Shared knowledge base (optional)
│   └── examples/                # Few-shot examples
│       ├── success_example1/
│       │   ├── code.md          # Example input code
│       │   ├── analysis.md      # Analysis result
│       │   ├── apis.md          # Suggested APIs
│       │   └── generated.md     # Generated output
│       ├── success_example2/
│       ├── failure_example1/
│       └── default_example1/
│
└── als/                          # Analysis prompts
    ├── system.md                 # System prompt for analysis
    ├── success_coverage.md       # Prompt for coverage analysis
    ├── failure_exception.md      # Prompt for exception analysis
    ├── knowledge/               # Shared knowledge base (optional)
    └── examples/                # Few-shot examples
        ├── coverage_example1/
        │   ├── code.md          # Example code
        │   ├── coverage.md      # Coverage result
        │   └── analysis.md      # Analysis output
        └── exception_example1/
            ├── code.md          # Example code
            ├── exception.md     # Exception message
            └── analysis.md      # Analysis output
```

## 🎯 Key Features

### 1. **Markdown-Based Templates**
- Clean, readable format
- Easy to edit and maintain
- Version control friendly

### 2. **Modular Examples**
- Each example in its own directory
- Components separated into individual files
- Easy to add/remove examples

### 3. **Template Variables**
Templates use `{{variable}}` syntax for placeholders:
- `{{lib}}` - Library name (pytorch/tensorflow)
- `{{code}}` - Generated or analyzed code
- `{{coverage}}` - Coverage information
- `{{exception}}` - Exception messages
- `{{als_res}}` - Analysis results
- `{{new_ops}}` - Suggested operators
- `{{op_nums}}` - Number of operators constraint
- `{{examples}}` - Formatted few-shot examples

## 🚀 Usage

The `prompts/` directory must exist in your project root. FUEL will load all prompts from this directory:

```bash
python -m fuel.fuzz --lib pytorch run_fuzz --max_round 1000
```

If the `prompts/` directory doesn't exist, FUEL will raise an error with instructions to create it.

## ✏️ Creating New Examples

### For Generation Prompts

1. Create a new directory in `prompts/gen/examples/`:
   ```bash
   mkdir prompts/gen/examples/success_example3
   ```

2. Add component files:
   - `code.md` - The example PyTorch model
   - `analysis.md` - Analysis of the result
   - `apis.md` - Suggested APIs (one per line)
   - `generated.md` - The generated output code

3. Examples are automatically loaded based on name prefix:
   - `success_*` → Used in success prompt
   - `failure_*` → Used in failure prompt
   - `default_*` → Used in default prompt

### For Analysis Prompts

1. Create a new directory in `prompts/als/examples/`:
   ```bash
   mkdir prompts/als/examples/coverage_example2
   ```

2. Add component files:
   - `code.md` - The example PyTorch model
   - `coverage.md` or `exception.md` - The result to analyze
   - `analysis.md` - The expected analysis output

3. Examples are loaded based on name prefix:
   - `coverage_*` → Used in coverage analysis
   - `exception_*` → Used in exception analysis

## 🔧 Advanced Customization

### Adding Knowledge Base

Create a `knowledge/` directory to store reusable knowledge:

```bash
mkdir prompts/gen/knowledge
echo "# Common PyTorch Patterns" > prompts/gen/knowledge/patterns.md
```

Then reference it in your templates using `{{knowledge}}`.

### Custom Template Loading

You can programmatically load and customize templates:

```python
from fuel.utils.prompt_loader import PromptLoader

loader = PromptLoader("prompts")
gen_prompts = loader.load_gen_prompts()
als_prompts = loader.load_als_prompts()

# Customize as needed
gen_prompts['success'] = gen_prompts['success'].replace("{{custom}}", "value")
```

## 📊 Example Naming Conventions

- `success_example1` - Successful execution with new coverage
- `success_example2` - Successful execution without new coverage  
- `failure_example1` - Invalid model that needs fixing
- `failure_example2` - Potential framework bug
- `failure_example3` - Type mismatch error
- `default_example1` - Simple baseline model
- `default_example2` - Complex model with multiple operators
- `coverage_example1` - High coverage example
- `exception_example1` - Runtime exception
- `exception_example2` - Compilation error

## 🎨 Best Practices

1. **Keep examples concise** - Focus on key patterns
2. **Use descriptive names** - Make intent clear from directory name
3. **Maintain consistency** - Follow the same structure across examples
4. **Test your prompts** - Verify examples work as expected
5. **Document special cases** - Add comments in markdown when needed

## 🔄 Migration from YAML

The old YAML format (`config/gen_prompt/*.yaml`, `config/als_prompt/*.yaml`) is no longer supported. All prompts must be in Markdown format in the `prompts/` directory.

If you need to reference old YAML prompts, they are preserved in the `config/` directory but are not loaded by FUEL.

## 📖 References

This prompt management system is inspired by:
- [KNighter](https://github.com/seclab-ucr/KNighter) - For the elegant Markdown-based approach
- [LangChain](https://github.com/langchain-ai/langchain) - For prompt template patterns

## 🤝 Contributing

When adding new examples or templates:
1. Follow the existing structure
2. Test with actual fuzzing runs
3. Document any new template variables
4. Keep examples self-contained and clear

