# GEPA Architecture Documentation

## 🏗️ System Architecture

### Overview

The GEPA Multi-Disease Antibody Optimization system implements a closed-loop evolutionary algorithm where:

1. An **Evaluator** scores sequences across multiple diseases
2. A **Feedback Generator** creates textual descriptions of performance
3. An **LLM** proposes mutations based on feedback
4. The **Adapter** orchestrates the cycle

```
┌─────────────────────────────────────────────────┐
│              GEPA Evolution Loop                │
│                                                 │
│  ┌──────────┐      ┌─────────────┐             │
│  │ Current  │─────>│  Evaluate   │             │
│  │ Sequence │      │ Multi-      │             │
│  └──────────┘      │ Disease     │             │
│       ▲            └─────────────┘             │
│       │                   │                    │
│       │                   ▼                    │
│       │            ┌─────────────┐             │
│       │            │  Generate   │             │
│       │            │  Feedback   │             │
│       │            └─────────────┘             │
│       │                   │                    │
│       │                   ▼                    │
│  ┌──────────┐      ┌─────────────┐             │
│  │   LLM    │<─────│  Build      │             │
│  │ Mutation │      │  Prompt     │             │
│  └──────────┘      └─────────────┘             │
│       │                                        │
│       └────────────────────────────────────────│
│                                                 │
└─────────────────────────────────────────────────┘
```

## 📦 Component Details

### 1. Data Layer (`load_abibench.py`)

**Purpose**: Load and organize the AbBiBench dataset

**Key Functions**:
- `load_abibench_data()`: Loads dataset from HuggingFace
- `build_lookup_table()`: Creates fast (antigen, sequence) → score mapping

**Data Flow**:
```
HuggingFace Dataset
    ↓
Extract Wildtype Seed
    ↓
Organize by Antigen
    ↓
Build Lookup Table
```

**Schema**:
```python
{
    'sequence': str,           # Amino acid sequence
    'antigen': str,            # Disease target
    'binding_score': float,    # Affinity measurement
    'mutation_type': str,      # 'WT' for wildtype
    'mutation': str            # Mutation description
}
```

---

### 2. Evaluator (`evaluator/`)

#### `affinity_model.py`

**Class**: `MultiDiseaseAffinityEvaluator`

**Purpose**: Score sequences against multiple diseases

**Key Methods**:
- `score(sequence, antigen)`: Get binding score for one disease
- `evaluate_all_antigens(sequence, antigens)`: Score across all diseases
- `aggregate_score(scores)`: Compute mean performance

**Implementation**:
```python
def score(self, sequence: str, antigen: str) -> float:
    key = (antigen, sequence)
    return self.lookup_table.get(key, 0.0)  # Default to 0.0 if not found
```

#### `feedback.py`

**Purpose**: Generate textual descriptions of mutations

**Key Functions**:
- `find_mutations()`: Identify amino acid changes
- `classify_amino_acid()`: Categorize by chemical properties
- `generate_feedback()`: Create structured feedback text

**Feedback Structure**:
```
=== DISEASE_NAME ===
✓/✗ Binding IMPROVED/DECREASED: old → new (+delta, +%)
Mutations (N):
  • Position X: A (type1) → B (type2)
  • Position Y: C (type3) → D (type4)
Interpretation: ...
```

---

### 3. LLM Client (`llm_client.py`)

**Class**: `LLMClient`

**Purpose**: Interface with OpenAI API

**Configuration**:
- Model selection (GPT-4, GPT-3.5-turbo, etc.)
- Temperature for creativity/consistency balance
- Max tokens for response length

**Key Method**:
```python
def generate(self, prompt: str) -> str:
    # Calls OpenAI API
    # Returns generated sequence
```

**Error Handling**:
- API key validation
- Connection error handling
- Response parsing

---

### 4. Adapter (`adapter/antibody_adapter.py`)

**Class**: `AntibodyAdapter`

**Purpose**: Core GEPA orchestration

**Key Methods**:

#### `evaluate_multi(sequence)`
```python
# Scores sequence across all target diseases
scores = {
    'HER2': 0.7234,
    'VEGF': 0.6891,
    'TNF': 0.7012
}
```

#### `build_multitask_feedback(old_seq, new_seq, old_scores, new_scores)`
```python
# Combines per-disease feedback into unified prompt
feedback = """
=== HER2 ===
✓ Binding IMPROVED: 0.7078 → 0.7234 (+0.0156)
...

=== VEGF ===
✓ Binding IMPROVED: 0.6657 → 0.6891 (+0.0234)
...

OVERALL SUMMARY
Average: 0.6909 → 0.7046
Improved: 2/3 diseases
"""
```

#### `propose_mutation(sequence, feedback)`
```python
# Builds prompt from template
# Calls LLM
# Validates and returns new sequence
```

#### `step(current_seq, current_scores)`
```python
# Complete GEPA iteration:
# 1. Build feedback
# 2. Propose mutation via LLM
# 3. Evaluate new sequence
# 4. Return results
```

**Validation**:
- Length preservation check
- Valid amino acid check
- Fallback to original if invalid

---

### 5. Baselines (`baselines/`)

#### `random_search.py`

**Strategy**: Random mutations

```python
for iteration in range(N):
    candidate = mutate_random(best_sequence, num_mutations)
    if score(candidate) > score(best):
        best = candidate
```

#### `single_mutation.py`

**Strategy**: Hill climbing with single-point mutations

```python
for iteration in range(N):
    all_neighbors = generate_single_mutations(current)
    best_neighbor = max(all_neighbors, key=score)
    if score(best_neighbor) > score(current):
        current = best_neighbor
```

#### `genetic_algorithm.py`

**Strategy**: Population-based evolution

```python
population = initialize()
for generation in range(N):
    fitness = evaluate(population)
    parents = select(population, fitness)
    offspring = crossover(parents)
    offspring = mutate(offspring)
    population = offspring + elites
```

---

## 🔄 GEPA Iteration Flow

### Detailed Step-by-Step

**Step 0: Initialization**
```python
current_seq = seed_sequence
current_scores = evaluate_multi(current_seq)
```

**Step 1: Performance Analysis**
```python
# Build feedback showing current state
for each antigen:
    score = current_scores[antigen]
    if score < threshold:
        feedback += f"{antigen} needs improvement"
```

**Step 2: LLM Mutation Proposal**
```python
prompt = template.format(
    sequence=current_seq,
    feedback=performance_analysis
)
new_seq = llm.generate(prompt)
```

**Step 3: Evaluation**
```python
new_scores = evaluate_multi(new_seq)
aggregate = mean(new_scores.values())
```

**Step 4: Comparative Feedback**
```python
feedback = build_multitask_feedback(
    old_seq=current_seq,
    new_seq=new_seq,
    old_scores=current_scores,
    new_scores=new_scores
)
```

**Step 5: Iteration**
```python
current_seq = new_seq
current_scores = new_scores
# Repeat from Step 1
```

---

## 🧬 Sequence Mutation Strategies

### LLM-Guided (GEPA)

**Advantages**:
- Context-aware mutations
- Multi-objective optimization
- Semantic understanding of amino acid properties
- Adaptive strategy based on feedback

**Prompt Engineering**:
```
You are an expert protein engineer...

Current sequence: {sequence}

Performance:
  HER2: 0.72 (strong)
  VEGF: 0.45 (weak) ← needs improvement
  TNF: 0.68 (moderate)

Task: Improve VEGF binding while maintaining others
Rules: 1-3 mutations, preserve length, valid amino acids
```

### Traditional Methods (Baselines)

**Random Search**:
- Pros: Simple, unbiased
- Cons: Inefficient, no learning

**Hill Climbing**:
- Pros: Systematic, guaranteed local improvement
- Cons: Stuck in local optima, slow

**Genetic Algorithm**:
- Pros: Population diversity, exploration
- Cons: Many evaluations, parameter tuning

---

## 📊 Evaluation Metrics

### Per-Disease Scores
```python
scores = {
    'HER2': 0.7234,
    'VEGF': 0.6891,
    'TNF': 0.7012
}
```

### Aggregate Score
```python
aggregate = mean(scores.values())
# = (0.7234 + 0.6891 + 0.7012) / 3
# = 0.7046
```

### Improvement Tracking
```python
delta = new_score - old_score
percent = (delta / old_score) * 100
improvements = count(diseases where delta > 0)
```

---

## 🔧 Configuration System

### YAML Structure

```yaml
llm:
  model: "gpt-4"
  temperature: 0.7           # Higher = more creative
  max_tokens: 500

dataset:
  name: "Exscientia/AbBiBench"
  
antigens:                    # Target diseases
  - "HER2"
  - "VEGF"
  - "TNF"

evolution:
  iterations: 10             # GEPA steps

mutation_prompt_template: |
  {prompt with {sequence} and {feedback} placeholders}
```

### Runtime Configuration

```python
config = load_config('config.yaml')

# Override programmatically
config['antigens'] = ['HER2', 'VEGF']
config['evolution']['iterations'] = 20
```

---

## 🚀 Extensibility

### Adding New Antigens

1. Update `config.yaml`:
```yaml
antigens:
  - "HER2"
  - "NEW_ANTIGEN"
```

2. Ensure dataset contains the antigen

### Custom Evaluators

Implement the interface:
```python
class CustomEvaluator:
    def score(self, sequence: str, antigen: str) -> float:
        # Your scoring logic
        pass
    
    def evaluate_all_antigens(self, sequence: str, antigens: list):
        # Multi-disease scoring
        pass
```

### Custom Baselines

Implement the `optimize()` method:
```python
class CustomBaseline:
    def optimize(self, seed_sequence: str):
        # Your optimization logic
        return best_sequence, best_scores, history
```

### Custom Feedback

Extend `feedback.py`:
```python
def generate_custom_feedback(...):
    # Add domain-specific insights
    # Include structural predictions
    # Reference known mutations
    pass
```

---

## 📈 Performance Considerations

### Computational Costs

**Per Iteration**:
- 1 LLM call (~1-2 seconds)
- N evaluations (N = number of antigens)
- Feedback generation (negligible)

**Total for 10 iterations**:
- ~10-20 seconds (LLM calls)
- Plus dataset loading (first run only)

### Optimization Tips

1. **Batch evaluation**: Evaluate multiple sequences at once
2. **Cache results**: Store computed scores
3. **Parallel baselines**: Run baselines concurrently
4. **Shorter sequences**: Use truncated sequences for testing

### Scalability

**More antigens**: Linear increase in evaluation time
**More iterations**: Linear increase in LLM calls
**Larger population**: Not applicable to GEPA (uses single sequence)

---

## 🔬 Research Directions

### Potential Enhancements

1. **Multi-sequence population**: Maintain diverse candidates
2. **Transfer learning**: Use mutations from one antigen for others
3. **Structural modeling**: Integrate 3D structure predictions
4. **Constraint handling**: Add manufacturability constraints
5. **Interactive evolution**: Human-in-the-loop feedback

### Experimental Ideas

1. Compare LLM models (GPT-4 vs GPT-3.5 vs Claude)
2. Test different prompt strategies
3. Hybrid: GEPA + Genetic Algorithm
4. Meta-learning: Learn from successful mutations
5. Multi-objective: Explicit Pareto optimization

---

## 📝 Code Quality

### Design Principles

- **Modularity**: Clear component separation
- **Extensibility**: Easy to add new features
- **Readability**: Self-documenting code
- **Robustness**: Error handling and validation

### Type Hints

```python
def evaluate_multi(
    self,
    sequence: str
) -> Dict[str, float]:
    ...
```

### Documentation

- Docstrings for all classes and functions
- Inline comments for complex logic
- Architecture documentation (this file)

---

## 🐛 Debugging Tips

### Common Issues

**"API key not found"**
```bash
export OPENAI_API_KEY='your-key'
```

**"Invalid sequence length"**
- Check LLM output parsing
- Validate extraction logic

**"Score is always 0.0"**
- Sequence not in dataset
- Check antigen spelling
- Verify lookup table construction

### Logging

Add detailed logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Testing Individual Components

```python
# Test evaluator
evaluator = MultiDiseaseAffinityEvaluator(lookup_table)
score = evaluator.score(sequence, 'HER2')

# Test feedback
feedback = generate_feedback(old_seq, new_seq, 0.7, 0.8)

# Test LLM (requires API key)
client = LLMClient(config)
response = client.generate("test prompt")
```

---

## 📚 References

- GEPA Framework: [Paper/Link]
- AbBiBench Dataset: HuggingFace Exscientia/AbBiBench
- OpenAI API: https://platform.openai.com/docs
- Protein Engineering: [Domain-specific references]

---

**Document Version**: 1.0  
**Last Updated**: 2025-11-17  
**Maintainer**: GEPA Development Team

