#!/usr/bin/env python3
"""
Test script to verify CV screening with system prompts
"""
import asyncio
import os
import json
from dotenv import load_dotenv

load_dotenv()

# Import after loading env
from advanced_app_v3 import call_openai_api_with_system
from system_prompts import CV_SCREENING_SYSTEM_PROMPT, SCREENING_USER_PROMPT

async def test_screening():
    print("="*80)
    print("TESTING CV SCREENING WITH SYSTEM PROMPT")
    print("="*80)
    
    # Test data
    resume_text = """
    Name: Madhu
    Email: madhu@example.com
    Phone: 9876543210
    
    PROFESSIONAL EXPERIENCE:
    Java Developer at TechCorp (2023-Present)
    - Developed microservices using Spring Boot 3.1
    - Built REST APIs with Java 11+
    - Experience with Maven, Git, Jenkins
    - Worked with Docker and Kubernetes
    - Familiar with JUnit and TestNG
    
    Junior Java Developer at DevSoft (2021-2023)
    - Core Java development
    - Database design with SQL
    - Agile methodologies
    
    SKILLS:
    - Java, Spring Boot, Spring MVC
    - REST APIs, Microservices
    - Maven, Git, Jenkins
    - Docker, Kubernetes
    - MySQL, PostgreSQL
    - Postman, REST testing
    - JUnit, TestNG
    
    EDUCATION:
    Bachelor's in Computer Science (2021)
    """
    
    jd_text = """
    POSITION: Automation Test Engineer (Selenium + Java)
    Experience Required: 3+ Years
    
    KEY RESPONSIBILITIES:
    - Develop, maintain, and execute automation test scripts using Selenium WebDriver and Java
    - Perform functional, regression, and integration testing
    - Build and enhance test automation frameworks (POM, TestNG, Maven)
    - Analyze test results, identify defects, track them using defect management tools
    - Collaborate with developers, QA teams, and business analysts
    - Integrate automation scripts with CI/CD tools such as Jenkins or GitLab CI
    - Prepare test documentation including test cases, test scenarios, and automation reports
    
    REQUIRED SKILLS:
    - 3+ years of hands-on experience in Automation Testing
    - Strong proficiency in Selenium WebDriver, Core Java, TestNG/JUnit
    - Experience with Maven, Git, Jenkins, or other CI/CD tools
    - Knowledge of automation frameworks using Page Object Model (POM)
    - Experience with API Testing (Postman / RestAssured) – preferred
    - Understanding of SDLC, STLC, and Agile methodologies
    - Strong debugging, analytical, and problem-solving skills
    """
    
    print("\n1. Resume provided: YES")
    print(f"2. JD provided: YES")
    print(f"3. Resume length: {len(resume_text)} chars")
    print(f"4. JD length: {len(jd_text)} chars")
    
    # Build user prompt
    user_prompt = SCREENING_USER_PROMPT.format(
        resume_text=resume_text,
        jd_text=jd_text
    )
    
    print(f"\n5. User prompt built: YES ({len(user_prompt)} chars)")
    print(f"6. System prompt loaded: YES ({len(CV_SCREENING_SYSTEM_PROMPT)} chars)")
    
    api_key = os.getenv('OPENAI_API_KEY')
    print(f"7. OpenAI API Key found: {'YES' if api_key else 'NO'}")
    model = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    print(f"8. Model: {model}")
    
    print("\n" + "="*80)
    print("CALLING OPENAI API...")
    print("="*80)
    
    result = await call_openai_api_with_system(
        CV_SCREENING_SYSTEM_PROMPT,
        user_prompt,
        timeout=20
    )
    
    print(f"\nAPI Response Status: {result.get('status')}")
    
    if result.get('status') == 'success':
        output = result.get('output', '')
        print(f"Output length: {len(output)} chars")
        print(f"\nRaw Output (first 500 chars):\n{output[:500]}")
        
        try:
            # Clean up markdown
            if '```json' in output:
                output = output.split('```json')[1].split('```')[0].strip()
            elif '```' in output:
                output = output.split('```')[1].split('```')[0].strip()
            
            parsed = json.loads(output)
            print(f"\n✓ JSON Parsed Successfully!")
            print(f"Score: {parsed.get('score')}")
            print(f"Decision: {parsed.get('decision')}")
            print(f"\nFull JSON response:")
            print(json.dumps(parsed, indent=2))
        except json.JSONDecodeError as e:
            print(f"\n✗ JSON Parse Error: {e}")
            print(f"Output was:\n{output}")
    else:
        print(f"Error: {result.get('error')}")

if __name__ == "__main__":
    asyncio.run(test_screening())
