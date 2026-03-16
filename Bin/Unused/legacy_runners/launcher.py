#!/usr/bin/env python
"""
Recruitment AI System - Interactive Launcher
"""

import os
import sys
import subprocess

def main():
    print('='*80)
    print('RECRUITMENT AI SYSTEM - LAUNCHER')
    print('='*80)
    print()
    
    # Check if we're in the right directory
    if not os.path.exists('main.py'):
        print('[ERROR] main.py not found. Please run this from the project directory.')
        sys.exit(1)
    
    print('What would you like to do?')
    print()
    print('1. Test the system (no credentials needed)')
    print('2. Run full application (requires .env credentials)')
    print('3. Check installation status')
    print('4. Create .env file from template')
    print('5. View documentation')
    print('6. Exit')
    print()
    
    choice = input('Enter your choice (1-6): ').strip()
    print()
    
    if choice == '1':
        print('[STARTING] Running test suite...')
        print('This will validate all models and components.')
        print()
        subprocess.run([sys.executable, 'test_final.py'])
    
    elif choice == '2':
        # Check if .env exists
        if not os.path.exists('.env'):
            print('[WARNING] .env file not found!')
            print()
            print('To run the full application, you need credentials.')
            print('Create .env file first:')
            print('  cp .env.example .env')
            print()
            print('Then edit .env with your API keys:')
            print('  - OPENAI_API_KEY')
            print('  - SUPABASE_URL')
            print('  - SUPABASE_KEY')
            print()
            response = input('Create .env file now? (y/n): ').strip().lower()
            if response == 'y':
                if os.path.exists('.env.example'):
                    with open('.env.example', 'r') as src:
                        with open('.env', 'w') as dst:
                            dst.write(src.read())
                    print('[SUCCESS] .env file created from template.')
                    print('Please edit .env with your credentials.')
                    input('Press Enter to continue...')
        
        print('[STARTING] Running full application...')
        print()
        subprocess.run([sys.executable, 'main.py'])
    
    elif choice == '3':
        print('[CHECKING] Installation status...')
        print()
        subprocess.run([sys.executable, '-m', 'pip', 'list', '--user'])
    
    elif choice == '4':
        if os.path.exists('.env.example'):
            if os.path.exists('.env'):
                response = input('.env already exists. Overwrite? (y/n): ').strip().lower()
                if response != 'y':
                    print('[CANCELLED]')
                    return
            
            with open('.env.example', 'r') as src:
                with open('.env', 'w') as dst:
                    dst.write(src.read())
            print('[SUCCESS] .env file created from template.')
            print()
            print('Next steps:')
            print('1. Edit .env file with your credentials')
            print('2. Add OPENAI_API_KEY')
            print('3. Add SUPABASE_URL and SUPABASE_KEY')
            print('4. Run: python launcher.py')
            print('5. Choose option 2 to start application')
        else:
            print('[ERROR] .env.example not found')
    
    elif choice == '5':
        print('[DOCUMENTATION]')
        print()
        docs = [
            ('QUICK_START.md', 'Quick start guide'),
            ('TEST_RESULTS.md', 'Test results and capabilities'),
            ('VERIFICATION_CHECKLIST.md', 'Verification details'),
            ('README.md', 'Full documentation'),
            ('API_REFERENCE.md', 'API reference'),
        ]
        for filename, description in docs:
            if os.path.exists(filename):
                print(f'[AVAILABLE] {filename:<30} - {description}')
            else:
                print(f'[NOT FOUND] {filename:<30} - {description}')
    
    elif choice == '6':
        print('[EXIT] Goodbye!')
        sys.exit(0)
    
    else:
        print('[ERROR] Invalid choice')
        sys.exit(1)


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print('[INTERRUPTED] User quit.')
        sys.exit(0)
    except Exception as e:
        print(f'[ERROR] {e}')
        sys.exit(1)
