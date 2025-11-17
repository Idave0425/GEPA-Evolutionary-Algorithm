# GEPA Multi-Disease Antibody Optimization

A multi-disease biological sequence optimization system using the **GEPA (Genetic Evolution via Prompting and Assessment)** framework. This system evolves antibody sequences using LLM-driven mutations and multi-disease evaluation.

## 🎯 Overview

This project implements an evolutionary algorithm that:

1. Starts with a seed antibody sequence from the AbBiBench dataset
2. Defines multiple target diseases/antigens (HER2, VEGF, TNF, etc.)
3. Evaluates binding affinity for each antigen
4. Generates textual feedback describing mutation effects
5. Uses an LLM to propose strategic mutations based on multi-disease feedback
6. Iteratively improves the antibody across all target diseases

## 🏗️ Architecture

### Core Components

```
.
├── config.yaml                    # Configuration file
├── main.py                        # Main runner script
├── llm_client.py                  # LLM API client wrapper
├── load_abibench.py              # Dataset loader
├── evaluator/
│   ├── affinity_model.py         # Multi-disease evaluator
│   └── feedback.py               # Feedback generation
├── adapter/
│   └── antibody_adapter.py       # Core GEPA logic
└── baselines/
    ├── random_search.py          # Random mutation baseline
    ├── single_mutation.py        # Hill climbing baseline
    └── genetic_algorithm.py      # GA baseline
```

### GEPA Loop

```
Current Sequence + Scores
    ↓
Generate Feedback (multi-disease)
    ↓
LLM Proposes Mutation
    ↓
Evaluate New Sequence
    ↓
Compare Performance
    ↓
Repeat
```

## 📦 Installation

### Requirements

- Python 3.10+
- OpenAI API key

### Setup

```bash
# Clone repository
cd GEPA-Evolutionary-Algorithm

# Install dependencies
pip install -r requirements.txt

# Set OpenAI API key
export OPENAI_API_KEY='your-api-key-here'
```

## 🚀 Usage

### Run GEPA Optimization

```bash
python main.py
```

The script will:
1. Load the AbBiBench dataset from HuggingFace
2. Extract the wildtype seed sequence
3. Initialize the multi-disease evaluator
4. Run GEPA iterations (default: 10)
5. Display progress and results
6. Optionally run baseline comparisons

### Configuration

Edit `config.yaml` to customize:

```yaml
# Target diseases
antigens:
  - "HER2"
  - "VEGF"
  - "TNF"

# Evolution settings
evolution:
  iterations: 10

# LLM settings
llm:
  model: "gpt-4"
  temperature: 0.7
```

## 📊 Dataset

The system uses the **AbBiBench** dataset from HuggingFace:

- **Dataset**: `Exscientia/AbBiBench`
- **Schema**:
  ```
  {
    "sequence": <amino acid sequence>,
    "antigen": <disease target>,
    "binding_score": <affinity score>,
    "mutation_type": <WT for wildtype>,
    ...
  }
  ```

## 🎯 Features

### Multi-Disease Optimization

- Evaluates sequences across multiple disease targets simultaneously
- Generates per-disease feedback
- Balances improvements across all targets

### Intelligent Feedback

Feedback includes:
- Binding score changes per disease
- Mutation details (position, amino acid changes)
- Chemical property analysis (hydrophobic, charged, etc.)
- Strategic guidance for next mutations

### Baseline Comparisons

Three baseline methods for comparison:

1. **Random Search**: Random mutations
2. **Single Mutation Hill Climbing**: Systematic single-point mutations
3. **Genetic Algorithm**: Population-based evolution

## 📈 Example Output

```
============================================================
ITERATION 5/10
============================================================

New Sequence:
  EVQLVESGGGLVQPGGSLRLSCAASGFTFSSYAMSWVRQAPGKGLEWVSAISGSG...

Performance:
  HER2: 0.7234 (↑ +0.0156)
  VEGF: 0.6891 (↑ +0.0234)
  TNF: 0.7012 (↓ -0.0045)
  Average: 0.7046 (+0.0115)

Feedback:
================================================================
=== HER2 ===
✓ Binding IMPROVED: 0.7078 → 0.7234 (+0.0156, +2.2%)
Mutations (2):
  • Position 23: V (hydrophobic) → T (polar)
  • Position 67: A (hydrophobic) → E (negatively charged)
Interpretation: These mutations positively affected binding...
================================================================
```

## 🔬 Evaluation Metrics

- **Per-Antigen Scores**: Individual binding affinity for each disease
- **Aggregate Score**: Mean binding across all antigens
- **Improvement Tracking**: Delta from seed sequence
- **Multi-Disease Coverage**: Number of diseases improved

## 🛠️ Development

### Adding New Antigens

Edit `config.yaml`:

```yaml
antigens:
  - "HER2"
  - "VEGF"
  - "TNF"
  - "YOUR_NEW_ANTIGEN"
```

### Customizing Mutation Prompts

Edit the `mutation_prompt_template` in `config.yaml` to adjust LLM behavior.

### Implementing New Baselines

Add new baseline classes in `baselines/` following the interface:

```python
class YourBaseline:
    def optimize(self, seed_sequence: str):
        # Return (best_sequence, best_scores, history)
        pass
```

## 📝 Citation

If you use this code, please cite the GEPA framework and AbBiBench dataset:

```bibtex
@article{gepa2024,
  title={GEPA: Genetic Evolution via Prompting and Assessment},
  author={...},
  year={2024}
}

@article{abbibench2024,
  title={AbBiBench: Antibody Binding Benchmark},
  author={Exscientia},
  year={2024}
}
```

## 📄 License

MIT License - see LICENSE file for details

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 🐛 Troubleshooting

### "API key not found"
- Ensure `OPENAI_API_KEY` is set: `export OPENAI_API_KEY='your-key'`

### "Dataset not found"
- Check internet connection
- Verify HuggingFace datasets library is installed
- Dataset will download automatically on first run

### "Invalid sequence length"
- LLM may return malformed sequences
- The system automatically validates and rejects invalid mutations
- Adjust `temperature` in config.yaml for more consistent outputs

## 📧 Contact

For questions or issues, please open a GitHub issue.

---

**Built with GEPA Framework | Powered by LLMs | Optimizing Biology**

