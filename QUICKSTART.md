# GEPA Quick Start Guide

## ⚡ 5-Minute Setup

### Step 1: Install Dependencies
```bash
pip install -r requirements.txt
```

### Step 2: Set API Key
```bash
export OPENAI_API_KEY='your-api-key-here'
```

### Step 3: Run
```bash
python main.py
```

That's it! 🎉

---

## 📋 Quick Commands

### Verify Setup
```bash
python verify_setup.py
```
Checks all dependencies and configuration.

### Run GEPA Optimization
```bash
python main.py
```
Full optimization with 10 iterations (default).

### Run Examples
```bash
python example_usage.py
```
Interactive examples showing different use cases.

### Setup Script
```bash
./setup.sh
```
Interactive setup with virtual environment option.

---

## 🎯 Common Tasks

### Change Target Diseases
Edit `config.yaml`:
```yaml
antigens:
  - "HER2"
  - "VEGF"
  - "TNF"
  - "YOUR_DISEASE"  # Add new disease
```

### Adjust Iterations
Edit `config.yaml`:
```yaml
evolution:
  iterations: 20  # Change from default 10
```

### Change LLM Model
Edit `config.yaml`:
```yaml
llm:
  model: "gpt-3.5-turbo"  # Faster, cheaper
  # or
  model: "gpt-4"          # Better quality
```

### Adjust Mutation Creativity
Edit `config.yaml`:
```yaml
llm:
  temperature: 0.3  # More conservative
  # or
  temperature: 0.9  # More creative
```

---

## 🔍 Troubleshooting

### Problem: "API key not found"
**Solution**:
```bash
export OPENAI_API_KEY='your-key'
# Or add to ~/.bashrc or ~/.zshrc for persistence
```

### Problem: "Dataset not found"
**Solution**: First run downloads dataset automatically. Requires internet connection.

### Problem: "Invalid sequence returned"
**Solutions**:
- Lower temperature in config.yaml
- Check mutation prompt template
- System auto-rejects invalid sequences

### Problem: "All scores are 0.0"
**Solutions**:
- Check antigen names match dataset
- Verify sequence is in dataset
- Try with known wildtype sequence

---

## 📊 Understanding Output

### Iteration Output
```
ITERATION 5/10
================

New Sequence:
  EVQLVESGGGLVQPGGSLRLSCAASGFTFS...

Performance:
  HER2: 0.7234 (↑ +0.0156)    # Improved
  VEGF: 0.6891 (↑ +0.0234)    # Improved
  TNF: 0.7012 (↓ -0.0045)     # Decreased
  Average: 0.7046 (+0.0115)   # Overall improvement
```

### Symbols
- `↑` = Improved
- `↓` = Decreased
- `=` = Unchanged
- `✓` = Positive result
- `✗` = Negative result

### Scores
- Range: 0.0 to 1.0+ (dataset dependent)
- Higher = better binding affinity
- 0.0 = sequence not found in dataset

---

## 🚀 Advanced Usage

### Programmatic Use
```python
from adapter import AntibodyAdapter
from evaluator import MultiDiseaseAffinityEvaluator
from llm_client import LLMClient

# Initialize components
evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
llm_client = LLMClient(config['llm'])
adapter = AntibodyAdapter(evaluator, llm_client, antigens, prompt)

# Run one iteration
new_seq, new_scores, feedback, agg = adapter.step(current_seq, current_scores)
```

### Evaluate Without LLM
```python
from evaluator import MultiDiseaseAffinityEvaluator

evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
scores = evaluator.evaluate_all_antigens(sequence, antigens)
```

### Run Specific Baseline
```python
from baselines import RandomSearchBaseline

baseline = RandomSearchBaseline(evaluator, antigens, iterations=20)
best_seq, best_scores, history = baseline.optimize(seed_sequence)
```

---

## 💡 Pro Tips

### 1. Start Small
Test with 2-3 iterations first:
```yaml
evolution:
  iterations: 3
```

### 2. Use Shorter Sequences
For testing, use sequence slices:
```python
test_seq = seed_sequence[:100]
```

### 3. Save Results
Redirect output to file:
```bash
python main.py > results.txt 2>&1
```

### 4. Compare Models
Test different LLM models:
- `gpt-4`: Best quality, slower, expensive
- `gpt-3.5-turbo`: Fast, cheap, good quality
- `gpt-4-turbo`: Balanced

### 5. Custom Prompts
Modify the prompt template in `config.yaml` for domain-specific guidance.

### 6. Batch Experiments
Create multiple config files:
```bash
python main.py --config config_experiment1.yaml
python main.py --config config_experiment2.yaml
```

---

## 📈 Performance Optimization

### Faster Iterations
```yaml
llm:
  model: "gpt-3.5-turbo"  # 5-10x faster than GPT-4
  max_tokens: 300         # Reduce from 500
```

### Parallel Baselines
Run baselines in separate terminals:
```bash
# Terminal 1
python -c "from baselines import RandomSearchBaseline; ..."

# Terminal 2
python -c "from baselines import GeneticAlgorithmBaseline; ..."
```

### Cache Dataset
Dataset is cached after first load in `~/.cache/huggingface/`

---

## 🎓 Learning Path

### Beginner
1. Run `verify_setup.py`
2. Run `python main.py` with defaults
3. Try `example_usage.py`
4. Modify config.yaml parameters

### Intermediate
1. Read ARCHITECTURE.md
2. Modify mutation prompt template
3. Add custom antigens
4. Compare with baselines

### Advanced
1. Implement custom evaluator
2. Create new baseline method
3. Extend feedback generation
4. Integrate with external tools

---

## 📦 Project Structure

```
GEPA-Evolutionary-Algorithm/
├── config.yaml              # Configuration
├── main.py                  # Main runner
├── llm_client.py           # LLM interface
├── load_abibench.py        # Data loader
├── evaluator/              # Scoring
│   ├── affinity_model.py
│   └── feedback.py
├── adapter/                # GEPA logic
│   └── antibody_adapter.py
├── baselines/              # Comparison methods
│   ├── random_search.py
│   ├── single_mutation.py
│   └── genetic_algorithm.py
├── requirements.txt        # Dependencies
├── README.md              # Overview
├── ARCHITECTURE.md        # Detailed docs
├── QUICKSTART.md          # This file
├── example_usage.py       # Examples
├── verify_setup.py        # Setup checker
└── setup.sh               # Setup script
```

---

## 🔗 Useful Links

- **OpenAI API**: https://platform.openai.com
- **HuggingFace Datasets**: https://huggingface.co/datasets
- **AbBiBench**: https://huggingface.co/datasets/Exscientia/AbBiBench

---

## ❓ Getting Help

### Check Setup
```bash
python verify_setup.py
```

### Read Documentation
- `README.md` - Project overview
- `ARCHITECTURE.md` - Technical details
- `QUICKSTART.md` - This file

### Debug Mode
Add print statements or use logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

---

## 🎯 Next Steps

After successful setup:

1. ✅ Run default optimization
2. ✅ Examine output and feedback
3. ✅ Try different antigens
4. ✅ Compare with baselines
5. ✅ Customize prompts
6. ✅ Extend for your use case

---

**Happy Optimizing! 🧬🚀**

