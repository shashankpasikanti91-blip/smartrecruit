DELETE FROM subscriptions WHERE user_id IN (SELECT id FROM auth_users WHERE email LIKE 'testverify_%');
DELETE FROM activity_log WHERE user_id IN (SELECT id FROM auth_users WHERE email LIKE 'testverify_%');
DELETE FROM auth_users WHERE email LIKE 'testverify_%';
SELECT name, email, role FROM auth_users ORDER BY created_at;
