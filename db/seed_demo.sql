-- Seed demo data for demo@srpailabs.com
-- User ID: 88881fe4-ab20-44e0-8856-6da2764d2595
-- Existing React Dev job ID: 0d03fd80-d5d5-4b76-9cf6-85d902d6a48d

-- Add 2 more demo jobs
INSERT INTO job_posts (user_id, title, company, location, type, description, requirements, status, ai_generated, tags, applications_count)
VALUES (
  '88881fe4-ab20-44e0-8856-6da2764d2595',
  'Digital Marketing Manager', 'SRP AI Labs', 'Hyderabad', 'full-time',
  'Lead our digital marketing efforts across SEO, paid media, content, and social channels. Drive brand awareness and lead generation for our SaaS products. Own the full marketing funnel.',
  '4+ years in digital marketing, Google Ads, Meta Ads, SEO/SEM, content strategy, analytics (GA4). Team management experience preferred.',
  'active', false, '{}', 0
) ON CONFLICT DO NOTHING;

INSERT INTO job_posts (user_id, title, company, location, type, description, requirements, status, ai_generated, tags, applications_count)
VALUES (
  '88881fe4-ab20-44e0-8856-6da2764d2595',
  'Business Development Executive', 'SRP AI Labs', 'Mumbai / Remote', 'full-time',
  'Join our fast-growing business development team to identify, qualify, and close new enterprise accounts. Manage the full sales cycle.',
  '2-5 years in B2B sales or business development. Excellent communication, CRM experience (Salesforce / HubSpot), proven track record.',
  'active', false, '{}', 0
) ON CONFLICT DO NOTHING;

-- Insert candidates for Senior React Developer job
INSERT INTO resumes (user_id, job_post_id, candidate_name, candidate_email, candidate_phone, ai_score, pipeline_stage, ai_skills, ai_summary, status)
VALUES
  (
    '88881fe4-ab20-44e0-8856-6da2764d2595',
    '0d03fd80-d5d5-4b76-9cf6-85d902d6a48d',
    'Priya Sharma', 'priya.sharma@demo.com', '+91 98765 43210',
    88, 'screening',
    ARRAY['React','TypeScript','Next.js','Node.js','REST APIs','Git'],
    'Strong Senior React developer with 6 years of experience currently at TCS. Excellent TypeScript and Next.js skills, very close match for the JD. Highly recommended.',
    'reviewed'
  ),
  (
    '88881fe4-ab20-44e0-8856-6da2764d2595',
    '0d03fd80-d5d5-4b76-9cf6-85d902d6a48d',
    'Arjun Mehta', 'arjun.mehta@demo.com', '+91 91234 56789',
    42, 'applied',
    ARRAY['React','JavaScript','HTML','CSS'],
    'Only 1.5 years of React experience; missing TypeScript and Next.js. Does not meet the 5-year senior requirement. Not suitable.',
    'reviewed'
  ),
  (
    '88881fe4-ab20-44e0-8856-6da2764d2595',
    '0d03fd80-d5d5-4b76-9cf6-85d902d6a48d',
    'Ananya Singh', 'ananya.singh@demo.com', '+91 94567 80123',
    93, 'offer',
    ARRAY['React','TypeScript','Next.js','GraphQL','AWS','Node.js','System Design'],
    'Eight years of React expertise, currently Senior SDE at Amazon. Outstanding TypeScript, Next.js, and system design skills. Top candidate — prioritise closing quickly.',
    'reviewed'
  );

-- Insert candidates for Digital Marketing Manager (get ID dynamically)
INSERT INTO resumes (user_id, job_post_id, candidate_name, candidate_email, candidate_phone, ai_score, pipeline_stage, ai_skills, ai_summary, status)
SELECT
  '88881fe4-ab20-44e0-8856-6da2764d2595',
  jp.id,
  'Neha Gupta', 'neha.gupta@demo.com', '+91 99887 76655',
  84, 'interview',
  ARRAY['SEO','Google Ads','Meta Ads','Content Strategy','GA4','SEM'],
  'Seven years of digital marketing experience leading multi-channel campaigns for fintech brands. Proficient in all required tools. Strong candidate, recommended for final round.',
  'reviewed'
FROM job_posts jp
WHERE jp.user_id = '88881fe4-ab20-44e0-8856-6da2764d2595' AND jp.title = 'Digital Marketing Manager';

-- Insert candidate for Business Development (get ID dynamically)
INSERT INTO resumes (user_id, job_post_id, candidate_name, candidate_email, candidate_phone, ai_score, pipeline_stage, ai_skills, ai_summary, status)
SELECT
  '88881fe4-ab20-44e0-8856-6da2764d2595',
  jp.id,
  'Rahul Kumar', 'rahul.kumar@demo.com', '+91 93456 78901',
  68, 'screening',
  ARRAY['B2B Sales','CRM','Salesforce','Negotiation','Cold Outreach'],
  '3 years in B2B SaaS sales, met quota in 2 of 3 years. Good communicator. Some gaps in enterprise deal closure but trainable. Proceed with caution.',
  'reviewed'
FROM job_posts jp
WHERE jp.user_id = '88881fe4-ab20-44e0-8856-6da2764d2595' AND jp.title = 'Business Development Executive';

-- Verify
SELECT 'Total jobs for demo user' as info, COUNT(*) FROM job_posts WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';
SELECT 'Total candidates for demo user' as info, COUNT(*) FROM resumes WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';
SELECT candidate_name, ai_score, pipeline_stage, status FROM resumes WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595' ORDER BY ai_score DESC;
