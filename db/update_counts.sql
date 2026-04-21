-- Update application counts for demo user's jobs
UPDATE job_posts jp 
SET applications_count = (
  SELECT COUNT(*) FROM resumes r WHERE r.job_post_id = jp.id
) 
WHERE jp.user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';

SELECT title, applications_count FROM job_posts WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';
