"""
Component Testing Script
Tests all major components without requiring API key or dataset download
"""

import sys

print("="*80)
print("GEPA COMPONENT TESTING")
print("="*80)

# Test 1: Validation utilities
print("\n[1/7] Testing validation utilities...")
try:
    from utils.validation import (
        validate_sequence,
        validate_antigen,
        is_valid_amino_acid_sequence,
        count_mutations,
        clean_sequence,
        VALID_AMINO_ACIDS
    )
    
    # Test valid sequence
    test_seq = "ACDEFGHIKLMNPQRSTVWY"
    is_valid, msg = validate_sequence(test_seq, strict=False)
    assert is_valid, f"Valid sequence rejected: {msg}"
    
    # Test invalid sequence
    invalid_seq = "ACDEFGHIKLMNPQRSTVWYX"
    is_valid, msg = validate_sequence(invalid_seq, strict=False)
    assert not is_valid, "Invalid sequence accepted"
    
    # Test mutation counting
    seq1 = "AAAA"
    seq2 = "AABA"
    assert count_mutations(seq1, seq2) == 1
    
    # Test sequence cleaning
    dirty = "ACE123FGH"
    clean = clean_sequence(dirty)
    assert clean == "ACEFGH"
    
    print("  ✓ Validation utilities working")
    
except Exception as e:
    print(f"  ✗ Validation utilities FAILED: {e}")
    sys.exit(1)

# Test 2: Evaluator with mock data
print("\n[2/7] Testing evaluator with mock data...")
try:
    from evaluator import MultiDiseaseAffinityEvaluator
    
    # Create mock lookup table
    mock_lookup = {
        ('HER2', 'ACDE'): 0.5,
        ('VEGF', 'ACDE'): 0.6,
        ('HER2', 'ACDF'): 0.7,
        ('VEGF', 'ACDF'): 0.8,
    }
    
    mock_antigens = ['HER2', 'VEGF']
    
    evaluator = MultiDiseaseAffinityEvaluator(mock_lookup, mock_antigens)
    
    # Test scoring
    scores = evaluator.evaluate_all_antigens('ACDE')
    assert scores['HER2'] == 0.5
    assert scores['VEGF'] == 0.6
    
    # Test aggregate
    agg = evaluator.aggregate_score(scores)
    assert agg == 0.55
    
    # Test caching
    assert evaluator.get_cache_size() == 1
    scores2 = evaluator.evaluate_all_antigens('ACDE')
    assert evaluator.get_cache_size() == 1  # Should be cached
    
    # Test unknown sequence
    scores3 = evaluator.evaluate_all_antigens('AAAA')
    assert scores3['HER2'] == 0.0
    assert scores3['VEGF'] == 0.0
    
    print("  ✓ Evaluator working")
    
except Exception as e:
    print(f"  ✗ Evaluator FAILED: {e}")
    sys.exit(1)

# Test 3: Feedback generation
print("\n[3/7] Testing feedback generation...")
try:
    from evaluator.feedback import (
        find_mutations,
        generate_multidisease_feedback,
        generate_initial_feedback,
        categorize_change
    )
    
    # Test mutation finding
    old = "ACDE"
    new = "ACDF"
    muts = find_mutations(old, new)
    assert len(muts) == 1
    assert muts[0] == (3, 'E', 'F')
    
    # Test change categorization
    assert "improvement" in categorize_change(0.1, 0.5).lower()
    assert "decrease" in categorize_change(-0.1, 0.5).lower()
    
    # Test multidisease feedback
    old_scores = {'HER2': 0.5, 'VEGF': 0.6}
    new_scores = {'HER2': 0.7, 'VEGF': 0.8}
    feedback = generate_multidisease_feedback(old, new, old_scores, new_scores, ['HER2', 'VEGF'])
    assert 'HER2' in feedback
    assert 'VEGF' in feedback
    assert 'E4F' in feedback or 'E3F' in feedback  # Mutation notation
    
    # Test initial feedback
    init_feedback = generate_initial_feedback("ACDE", {'HER2': 0.3, 'VEGF': 0.7}, ['HER2', 'VEGF'])
    assert 'HER2' in init_feedback
    assert 'VEGF' in init_feedback
    
    print("  ✓ Feedback generation working")
    
except Exception as e:
    print(f"  ✗ Feedback generation FAILED: {e}")
    sys.exit(1)

# Test 4: Adapter (without LLM)
print("\n[4/7] Testing adapter components...")
try:
    from adapter import AntibodyAdapter
    
    # Mock LLM client
    class MockLLMClient:
        def generate(self, prompt):
            # Return a simple mutation
            return "ACDF"  # Changed E to F
    
    mock_llm = MockLLMClient()
    
    adapter = AntibodyAdapter(
        evaluator=evaluator,
        llm_client=mock_llm,
        mutation_prompt_template="Test: {sequence}\n{feedback}",
        max_mutations=3
    )
    
    # Test evaluation
    scores = adapter.evaluate_multi('ACDE')
    assert 'HER2' in scores
    assert 'VEGF' in scores
    
    # Test aggregate
    agg = adapter.aggregate_score(scores)
    assert agg == 0.55
    
    # Test sequence extraction
    raw = "```\nACDF\n```"
    extracted = adapter._extract_sequence(raw, expected_length=4)
    assert extracted == "ACDF"
    
    # Test sequence extraction with labels
    raw2 = "Mutated sequence: ACDF"
    extracted2 = adapter._extract_sequence(raw2, expected_length=4)
    assert extracted2 == "ACDF"
    
    print("  ✓ Adapter components working")
    
except Exception as e:
    print(f"  ✗ Adapter FAILED: {e}")
    sys.exit(1)

# Test 5: Baselines with mock data
print("\n[5/7] Testing baselines...")
try:
    from baselines import RandomSearchBaseline, SingleMutationBaseline, GeneticAlgorithmBaseline
    
    # Random Search
    rs = RandomSearchBaseline(evaluator, iterations=2, mutations_per_iter=1)
    best_seq, best_scores, history = rs.optimize('ACDE')
    assert len(history) == 3  # 0 + 2 iterations
    assert 'aggregate' in history[0]
    print("  ✓ Random Search working")
    
    # Single Mutation
    sm = SingleMutationBaseline(evaluator, iterations=2, sample_size=5)
    best_seq, best_scores, history = sm.optimize('ACDE')
    assert len(history) == 3
    assert 'aggregate' in history[0]
    print("  ✓ Single Mutation working")
    
    # Genetic Algorithm
    ga = GeneticAlgorithmBaseline(evaluator, population_size=5, generations=2)
    best_seq, best_scores, history = ga.optimize('ACDE')
    assert len(history) == 2
    assert 'aggregate' in history[0]
    print("  ✓ Genetic Algorithm working")
    
except Exception as e:
    print(f"  ✗ Baselines FAILED: {e}")
    sys.exit(1)

# Test 6: Config loading
print("\n[6/7] Testing config loading...")
try:
    try:
        import yaml
    except ImportError:
        print("  ⚠️  PyYAML not installed (run: pip install pyyaml)")
        print("  ⊙ Skipping config test")
    else:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required fields
        assert 'llm' in config
        assert 'dataset' in config
        assert 'antigens' in config
        assert 'evolution' in config
        assert 'mutation_prompt_template' in config
        
        # Check new fields
        assert 'run_baselines' in config
        assert config['llm']['temperature'] == 0.2
        assert config['llm']['max_mutations'] == 3
        
        print("  ✓ Config loading working")
    
except Exception as e:
    print(f"  ✗ Config loading FAILED: {e}")
    sys.exit(1)

# Test 7: Import structure
print("\n[7/7] Testing import structure...")
try:
    # Test clean imports
    from evaluator import MultiDiseaseAffinityEvaluator
    from adapter import AntibodyAdapter
    from baselines import RandomSearchBaseline, SingleMutationBaseline, GeneticAlgorithmBaseline
    from utils import validate_sequence, VALID_AMINO_ACIDS
    
    print("  ✓ Import structure working")
    
except Exception as e:
    print(f"  ✗ Import structure FAILED: {e}")
    sys.exit(1)

# Summary
print("\n" + "="*80)
print("ALL TESTS PASSED ✓")
print("="*80)
print("\nComponents are working correctly!")
print("\nTo run the full system:")
print("1. Set your OpenAI API key: export OPENAI_API_KEY='your-key'")
print("2. Run: python3 main.py")
print("\nNote: The first run will download the AbBiBench dataset from HuggingFace.")

