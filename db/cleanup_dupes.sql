-- Clean up duplicate jobs and candidates for demo user

-- First delete resumes for duplicate job posts (keeping earliest)
DELETE FROM resumes WHERE job_post_id IN (
  'cba259ad-9295-4c81-a0c8-50f4da50eba0',
  '7781042a-eabd-4770-949b-824160dc118b'
);

-- Delete the duplicate job posts themselves
DELETE FROM job_posts WHERE id IN (
  'cba259ad-9295-4c81-a0c8-50f4da50eba0',
  '7781042a-eabd-4770-949b-824160dc118b'
);

-- Also remove duplicate resumes for the React Dev job (keep first by created_at for each candidate)
DELETE FROM resumes
WHERE id NOT IN (
  SELECT DISTINCT ON (candidate_email) id
  FROM resumes
  WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595'
  ORDER BY candidate_email, created_at ASC
)
AND user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';

-- Verify final state
SELECT 'Jobs' as entity, COUNT(*) FROM job_posts WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';
SELECT 'Candidates' as entity, COUNT(*) FROM resumes WHERE user_id = '88881fe4-ab20-44e0-8856-6da2764d2595';

SELECT r.candidate_name, r.ai_score, r.pipeline_stage, jp.title as job
FROM resumes r
LEFT JOIN job_posts jp ON jp.id = r.job_post_id
WHERE r.user_id = '88881fe4-ab20-44e0-8856-6da2764d2595'
ORDER BY r.ai_score DESC;
