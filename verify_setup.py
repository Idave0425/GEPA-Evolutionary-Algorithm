"""
Verification script to check if setup is correct
Tests all components without requiring OpenAI API key
"""

import sys
import yaml


def check_python_version():
    """Check Python version"""
    print("[1/6] Checking Python version...")
    version = sys.version_info
    
    if version.major >= 3 and version.minor >= 10:
        print(f"  ✓ Python {version.major}.{version.minor}.{version.micro}")
        return True
    else:
        print(f"  ✗ Python {version.major}.{version.minor}.{version.micro} (requires 3.10+)")
        return False


def check_dependencies():
    """Check if all dependencies are installed"""
    print("\n[2/6] Checking dependencies...")
    
    required = {
        'openai': 'openai',
        'datasets': 'datasets',
        'yaml': 'pyyaml',
        'numpy': 'numpy'
    }
    
    all_ok = True
    for module, package in required.items():
        try:
            __import__(module)
            print(f"  ✓ {package}")
        except ImportError:
            print(f"  ✗ {package} (not installed)")
            all_ok = False
    
    return all_ok


def check_config():
    """Check if config file is valid"""
    print("\n[3/6] Checking configuration...")
    
    try:
        with open('config.yaml', 'r') as f:
            config = yaml.safe_load(f)
        
        # Check required fields
        required_fields = ['llm', 'dataset', 'antigens', 'evolution', 'mutation_prompt_template']
        for field in required_fields:
            if field not in config:
                print(f"  ✗ Missing field: {field}")
                return False
        
        print(f"  ✓ config.yaml is valid")
        print(f"  ✓ Target antigens: {', '.join(config['antigens'])}")
        print(f"  ✓ Iterations: {config['evolution']['iterations']}")
        return True
        
    except FileNotFoundError:
        print("  ✗ config.yaml not found")
        return False
    except Exception as e:
        print(f"  ✗ Error reading config: {e}")
        return False


def check_modules():
    """Check if project modules can be imported"""
    print("\n[4/6] Checking project modules...")
    
    modules_to_test = [
        'llm_client',
        'load_abibench',
        'evaluator',
        'adapter',
        'baselines'
    ]
    
    all_ok = True
    for module in modules_to_test:
        try:
            __import__(module)
            print(f"  ✓ {module}")
        except ImportError as e:
            print(f"  ✗ {module}: {e}")
            all_ok = False
    
    return all_ok


def check_dataset():
    """Try to load dataset (may take time on first run)"""
    print("\n[5/6] Checking dataset access...")
    
    try:
        from datasets import load_dataset
        
        print("  Attempting to load AbBiBench...")
        print("  (This may take a while on first run)")
        
        dataset = load_dataset("Exscientia/AbBiBench", split="train")
        
        print(f"  ✓ Dataset loaded successfully")
        print(f"  ✓ Total entries: {len(dataset)}")
        
        # Check for required fields
        if len(dataset) > 0:
            first_entry = dataset[0]
            required_fields = ['sequence', 'antigen', 'binding_score']
            for field in required_fields:
                if field in first_entry:
                    print(f"  ✓ Field '{field}' present")
                else:
                    print(f"  ✗ Field '{field}' missing")
                    return False
        
        return True
        
    except Exception as e:
        print(f"  ✗ Error loading dataset: {e}")
        print("  Note: Dataset will be downloaded on first run")
        return False


def check_api_key():
    """Check if OpenAI API key is set"""
    print("\n[6/6] Checking OpenAI API key...")
    
    import os
    
    api_key = os.getenv('OPENAI_API_KEY')
    if api_key:
        # Don't print the actual key
        masked = api_key[:8] + "..." + api_key[-4:] if len(api_key) > 12 else "***"
        print(f"  ✓ OPENAI_API_KEY is set ({masked})")
        return True
    else:
        print("  ⚠️  OPENAI_API_KEY not set")
        print("  Note: Required to run GEPA optimization")
        print("  Set with: export OPENAI_API_KEY='your-key-here'")
        return False


def main():
    """Run all verification checks"""
    print("="*60)
    print("GEPA Setup Verification")
    print("="*60)
    print()
    
    results = {
        'Python version': check_python_version(),
        'Dependencies': check_dependencies(),
        'Configuration': check_config(),
        'Project modules': check_modules(),
        'Dataset access': check_dataset(),
        'API key': check_api_key()
    }
    
    print("\n" + "="*60)
    print("Summary")
    print("="*60)
    
    for check, status in results.items():
        symbol = "✓" if status else "✗"
        print(f"{symbol} {check}")
    
    all_passed = all(results.values())
    critical_passed = all([
        results['Python version'],
        results['Dependencies'],
        results['Configuration'],
        results['Project modules']
    ])
    
    print("\n" + "="*60)
    
    if all_passed:
        print("✓ All checks passed! Ready to run.")
        print("\nRun the optimizer with:")
        print("  python main.py")
        return 0
    elif critical_passed:
        print("⚠️  Core setup complete, but some optional checks failed.")
        print("You can still run the optimizer, but some features may not work.")
        return 0
    else:
        print("✗ Setup incomplete. Please fix the errors above.")
        print("\nTo install dependencies:")
        print("  pip install -r requirements.txt")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)

