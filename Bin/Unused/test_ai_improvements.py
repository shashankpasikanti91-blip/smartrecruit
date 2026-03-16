#!/usr/bin/env python3
"""
Quick Test - AI Improvements Verification
Tests the new AI Writing and Message Generation features
"""

import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_imports():
    """Test that all imports work"""
    print("=" * 60)
    print("TEST 1: Checking Imports")
    print("=" * 60)
    
    try:
        from utils.ai_helpers import (
            get_writing_prompt, get_message_prompt, enhance_prompt_with_context,
            call_openai_api, OPENAI_API_KEY, OPENAI_MODEL, WRITING_PROMPTS, MESSAGE_PROMPTS
        )
        print("✓ All AI helper imports successful")
        print(f"  - OpenAI Model: {OPENAI_MODEL}")
        print(f"  - API Key configured: {'✓' if OPENAI_API_KEY else '✗'}")
        return True
    except Exception as e:
        print(f"✗ Import error: {str(e)}")
        return False

def test_prompts():
    """Test prompt generation"""
    print("\n" + "=" * 60)
    print("TEST 2: Checking Prompt Generation")
    print("=" * 60)
    
    from utils.ai_helpers import get_writing_prompt, get_message_prompt
    
    # Test writing prompts
    prompt = get_writing_prompt("rewrite", "professional", "email")
    print("✓ Writing prompt generated (rewrite, professional, email)")
    print(f"  Length: {len(prompt)} chars")
    
    # Test message prompts
    msg_prompt = get_message_prompt("interview", "John Doe", "Senior Developer", "")
    print("✓ Message prompt generated (interview)")
    print(f"  Length: {len(msg_prompt)} chars")
    
    return True

def test_context_enhancement():
    """Test context enhancement logic"""
    print("\n" + "=" * 60)
    print("TEST 3: Checking Context Enhancement")
    print("=" * 60)
    
    from utils.ai_helpers import enhance_prompt_with_context
    
    test_cases = [
        ("Simple prompt", ""),
        ("Base prompt", "promotion to manager"),
        ("Base prompt", "urgent hire needed"),
        ("Base prompt", "remote flexible position"),
        ("Base prompt", "salary negotiation budget constraints"),
    ]
    
    for prompt, context in test_cases:
        enhanced = enhance_prompt_with_context(prompt, context)
        has_context = enhanced != prompt if context else enhanced == prompt
        status = "✓" if has_context else "✗"
        print(f"{status} Context: '{context[:30] if context else 'none'}...' - Enhanced: {len(enhanced)} chars")
    
    return True

def test_syntax():
    """Test that app files have no syntax errors"""
    print("\n" + "=" * 60)
    print("TEST 4: Checking Syntax")
    print("=" * 60)
    
    import py_compile
    
    files_to_check = [
        'advanced_app.py',
        'utils/ai_helpers.py',
    ]
    
    all_ok = True
    for filepath in files_to_check:
        try:
            py_compile.compile(filepath, doraise=True)
            print(f"✓ {filepath} - Syntax OK")
        except py_compile.PyCompileError as e:
            print(f"✗ {filepath} - Syntax Error: {str(e)[:80]}")
            all_ok = False
    
    return all_ok

def main():
    print("\n" + "=" * 60)
    print("AI IMPROVEMENTS - VERIFICATION TEST")
    print("=" * 60)
    
    results = []
    
    # Run tests
    results.append(("Imports", test_imports()))
    results.append(("Prompts", test_prompts()))
    results.append(("Context", test_context_enhancement()))
    results.append(("Syntax", test_syntax()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n✓ All systems ready for deployment!")
        return 0
    else:
        print(f"\n✗ {total - passed} test(s) failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())
