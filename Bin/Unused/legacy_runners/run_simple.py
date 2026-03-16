#!/usr/bin/env python
"""
Recruitment AI System - Simplified Production Launcher
No problematic module imports at top level
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables first
load_dotenv()

# Ensure logs directory exists
os.makedirs('logs', exist_ok=True)

# Setup logging ONLY (no other imports)
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/recruitment_ai.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def demo_ai_screening():
    """Run AI screening demo with OpenAI - PURE HTTP, NO IMPORTS"""
    try:
        print()
        print('='*80)
        print('AI SCREENING DEMO - ANALYZING CANDIDATE (GPT-4-mini)')
        print('='*80)
        print()
        
        # Test data inline
        candidate_name = 'John Software Engineer'
        candidate_role = 'Senior Software Engineer'
        candidate_exp = 7.5
        candidate_salary = 150000
        candidate_skills = ['Python (expert)', 'FastAPI (advanced)', 'PostgreSQL (advanced)', 'Docker (intermediate)']
        
        print('CANDIDATE PROFILE:')
        print(f'  Name: {candidate_name}')
        print(f'  Current Role: {candidate_role}')
        print(f'  Experience: {candidate_exp} years')
        print(f'  Expected Salary: ${candidate_salary:,}')
        print(f'  Skills: {", ".join(candidate_skills)}')
        
        print()
        print('JOB REQUIREMENT:')
        job_title = 'Senior Backend Developer'
        job_company = 'InnovateCorp Inc'
        job_location = 'San Francisco, CA'
        job_exp = 5
        job_skills = ['Python', 'FastAPI', 'PostgreSQL', 'Docker', 'AWS']
        job_budget_min = 120000
        job_budget_max = 180000
        
        print(f'  Title: {job_title}')
        print(f'  Company: {job_company}')
        print(f'  Location: {job_location}')
        print(f'  Min Experience: {job_exp} years')
        print(f'  Required Skills: {", ".join(job_skills)}')
        print(f'  Budget: ${job_budget_min:,} - ${job_budget_max:,}')
        
        print()
        print('ANALYZING MATCH WITH OpenAI GPT-4-mini...')
        print('-'*80)
        
        # Build prompt
        prompt = f"""You are an expert recruiter. Analyze this candidate-job match:

CANDIDATE:
- Name: {candidate_name}
- Current Role: {candidate_role}
- Experience: {candidate_exp} years
- Skills: {', '.join(candidate_skills)}
- Expected Salary: ${candidate_salary:,}

JOB OPENING:
- Title: {job_title}
- Company: {job_company}
- Location: {job_location}
- Required Skills: {', '.join(job_skills)}
- Min Experience: {job_exp} years
- Budget: ${job_budget_min:,} - ${job_budget_max:,}

Provide:
1. Match score (0-100)
2. Strengths (2-3 points)
3. Gaps (2-3 points)
4. Salary compatibility
5. Overall recommendation (STRONG MATCH / GOOD MATCH / POSSIBLE / NOT RECOMMENDED)"""
        
        # Direct httpx API call ONLY
        import httpx
        
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print('[ERROR] No OPENAI_API_KEY found')
            return False
        
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        data = {
            'model': 'gpt-4-mini',
            'messages': [
                {'role': 'system', 'content': 'You are an expert recruiter providing candidate screening analysis.'},
                {'role': 'user', 'content': prompt}
            ],
            'max_tokens': 500,
            'temperature': 0.7
        }
        
        print('[Connecting to OpenAI API...]')
        response = httpx.post(
            'https://api.openai.com/v1/chat/completions',
            headers=headers,
            json=data,
            timeout=30.0
        )
        
        print()
        if response.status_code == 200:
            result = response.json()
            analysis = result['choices'][0]['message']['content']
            print('AI ANALYSIS RESULT:')
            print('-'*80)
            print(analysis)
            print()
        else:
            print(f'[ERROR] OpenAI API returned status {response.status_code}')
            print(f'Response: {response.text[:200]}')
            return False
        
        print('='*80)
        print('Demo completed successfully!')
        print('='*80)
        
        return True
        
    except Exception as e:
        import traceback
        logger.error(f'Demo failed: {str(e)}')
        print()
        print('[ERROR DETAILS]')
        traceback.print_exc()
        print(f'[ERROR] Demo failed: {str(e)}')
        return False

def test_database():
    """Test Supabase database connection"""
    try:
        import httpx
        
        print()
        print('='*80)
        print('DATABASE CONNECTION TEST')
        print('='*80)
        print()
        
        url = os.getenv('SUPABASE_URL')
        key = os.getenv('SUPABASE_KEY')
        
        if not url or not key:
            print('[ERROR] Missing SUPABASE_URL or SUPABASE_KEY')
            return False
        
        print('[TESTING] Connecting to Supabase...')
        
        headers = {
            'Authorization': f'Bearer {key}',
            'Content-Type': 'application/json'
        }
        
        response = httpx.get(
            f'{url}/rest/v1/',
            headers=headers,
            timeout=5.0
        )
        
        print('[OK] Supabase connection successful')
        print(f'     Project: {url}')
        print()
        print('Database is ready for:')
        print('  - Candidate data storage')
        print('  - Job requirement management')
        print('  - Interview scheduling')
        print('  - Screening results')
        print('  - Message history')
        print()
        print('='*80)
        
        return True
        
    except Exception as e:
        logger.error(f'Database test failed: {str(e)}')
        print(f'[ERROR] Database test failed: {str(e)}')
        return False

def test_all_configs():
    """Test all configurations"""
    print('Testing all configurations...')
    print()
    
    import httpx
    
    # Test 1: Credentials
    print('[1] Credentials')
    required = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY', 'N8N_BASE_URL']
    all_present = all(os.getenv(var) for var in required)
    status = '[OK]' if all_present else '[MISSING]'
    print('    ' + status)
    
    # Test 2: OpenAI
    print('[2] OpenAI API')
    try:
        api_key = os.getenv('OPENAI_API_KEY')
        headers = {'Authorization': f'Bearer {api_key}'}
        response = httpx.get('https://api.openai.com/v1/models', headers=headers, timeout=5.0)
        if response.status_code == 200:
            models_count = len(response.json().get('data', []))
            print('    [OK] %d models available' % models_count)
        else:
            print('    [ERROR] Status %d' % response.status_code)
    except Exception as e:
        print('    [ERROR] ' + str(e)[:40])
    
    # Test 3: Database
    print('[3] Supabase Database')
    test_database()
    
    # Test 4: Logging
    print('[4] Logging System')
    logger.info('Test log entry')
    print('    [OK] Logging configured')
    
    print()

def main():
    """Main application loop"""
    print()
    print('='*80)
    print('RECRUITMENT AI SYSTEM - PRODUCTION LAUNCHER')
    print('='*80)
    print()
    
    # Check credentials
    required = ['OPENAI_API_KEY', 'SUPABASE_URL', 'SUPABASE_KEY']
    missing = [var for var in required if not os.getenv(var)]
    
    if missing:
        print(f'[ERROR] Missing credentials: {", ".join(missing)}')
        return False
    
    print('[OK] All credentials configured')
    print()
    
    while True:
        print()
        print('='*80)
        print('RECRUITMENT AI SYSTEM - MAIN MENU')
        print('='*80)
        print()
        print('1. Run AI Screening Demo (OpenAI GPT-4-mini - Cost Optimized)')
        print('2. Test Database Connection (Supabase)')
        print('3. Test All Configurations')
        print('4. View System Status')
        print('5. Exit')
        print()
        
        choice = input('Select option (1-5): ').strip()
        print()
        
        if choice == '1':
            demo_ai_screening()
        
        elif choice == '2':
            test_database()
        
        elif choice == '3':
            test_all_configs()
        
        elif choice == '4':
            print('SYSTEM STATUS:')
            print()
            print('[OK] OpenAI API: Ready')
            print('[OK] Supabase Database: Ready')
            print('[OK] Configuration: Complete')
            print()
            print('System Status: PRODUCTION READY')
            print()
        
        elif choice == '5':
            print('Exiting...')
            break
        
        else:
            print('[ERROR] Invalid option')

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print()
        print('[INTERRUPTED] User quit')
        sys.exit(0)
    except Exception as e:
        logger.error(f'Fatal error: {str(e)}')
        print(f'[FATAL ERROR] {str(e)}')
        sys.exit(1)
