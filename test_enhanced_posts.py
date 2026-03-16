#!/usr/bin/env python3
"""
Test the enhanced detailed job post generation
"""
import requests
import json

BASE_URL = "http://localhost:5003"

def test_detailed_job_posts():
    """Test enhanced detailed job post generation"""
    print("🔧 Testing Enhanced Detailed Job Post Generation...")
    
    # Application Engineer test payload (similar to user's example)
    test_payload = {
        "jd_text": """Application Engineer - Data Center Infrastructure

We are seeking an experienced Application Engineer to join our team and support our growing data center infrastructure business. 

Key Responsibilities:
- Work closely with sales team to propose comprehensive Data Center infrastructure solutions
- Provide expert technical support during the pre-sales process and customer consultations  
- Develop and customize technical solutions involving UPS systems, PDU, server racks, and cable management
- Create detailed technical proposals, system layouts, and specifications using AutoCAD
- Conduct site surveys and assessments for data center facility requirements
- Stay current with industry trends, emerging technologies, and best practices
- Collaborate with engineering teams on solution design and implementation
- Support post-sales technical queries and system optimization

Required Qualifications:
- Bachelor's degree in Electrical Engineering, Mechanical Engineering, or related technical field
- 3+ years of experience in data center design, electrical infrastructure, or similar technical roles
- Strong knowledge of UPS systems, power distribution, cooling systems, and data center equipment
- Proficiency in AutoCAD, Visio, and Microsoft Office suite
- Excellent communication and presentation skills with ability to explain complex technical concepts
- Strong project management skills and ability to handle multiple concurrent projects
- Understanding of industry standards and regulations for data center facilities

Preferred Qualifications:
- Experience with cooling concepts and environmental control systems
- Knowledge of energy efficiency principles and sustainability practices  
- Previous experience in pre-sales technical support or consulting roles
- Professional certifications in relevant technologies

Company: Leading data center solutions provider
Location: Flexible - Remote/Onsite options available
Type: Permanent, Full-time
Industry: Data Center Infrastructure & Technology Solutions""",
        "job_title": "Application Engineer - Data Center Infrastructure"
    }
    
    try:
        print(f"📡 Making request to {BASE_URL}/api/generate-job-post")
        response = requests.post(
            f"{BASE_URL}/api/generate-job-post",
            json=test_payload,
            timeout=90
        )
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status') == 'success' and 'data' in result:
                data = result['data']
                
                print("✅ Enhanced posts generated successfully!")
                
                # Check LinkedIn post length and content
                linkedin = data.get('linkedin_post', '')
                linkedin_words = len(linkedin.split())
                print(f"📱 LinkedIn Post: {linkedin_words} words")
                if linkedin_words >= 250:
                    print("✅ LinkedIn: Good length (250+ words)")
                else:
                    print("⚠️ LinkedIn: Still too short")
                print(f"Preview: {linkedin[:150]}...")
                
                # Check Indeed post length and content
                indeed = data.get('indeed_post', '')
                indeed_words = len(indeed.split())
                print(f"\n💼 Indeed Post: {indeed_words} words")
                if indeed_words >= 250:
                    print("✅ Indeed: Good length (250+ words)")
                else:
                    print("⚠️ Indeed: Still too short")
                print(f"Preview: {indeed[:150]}...")
                
                # Check WhatsApp post length and content
                whatsapp = data.get('whatsapp_post', '')
                whatsapp_words = len(whatsapp.split())
                print(f"\n💬 WhatsApp Post: {whatsapp_words} words")
                if whatsapp_words >= 180:
                    print("✅ WhatsApp: Good length (180+ words)")
                else:
                    print("⚠️ WhatsApp: Still too short")
                print(f"Preview: {whatsapp[:150]}...")
                
                # Check Email post 
                email = data.get('email_post', '')
                email_words = len(email.split())
                print(f"\n📧 Email Post: {email_words} words")
                if email_words >= 250:
                    print("✅ Email: Good length (250+ words)")
                else:
                    print("⚠️ Email: Needs more content")
                
                # Summary
                if linkedin_words >= 250 and indeed_words >= 250 and whatsapp_words >= 180:
                    print("\n🎉 SUCCESS! All posts are now detailed and comprehensive!")
                else:
                    print("\n⚠️ Some posts still need more detail. Checking system prompt...")
                    
                return True
            else:
                print(f"❌ Response issue: {result}")
                return False
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Enhanced Job Post Detail Test")
    print("="*50)
    
    import time
    print("⏳ Waiting for server...")
    time.sleep(3)
    
    success = test_detailed_job_posts()
    
    print("\n" + "="*50)
    if success:
        print("✅ Test completed - Check results above")
    else:
        print("❌ Test failed - Server might need restart")