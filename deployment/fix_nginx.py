import paramiko
HOST='5.223.67.236'; USER='root'; PASS='856Reey@nsh'
client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

# Fix nginx: add all Next.js API routes to the proxy_pass next.js block
OLD = r'location ~ \^/api/(screen\|parse\|jobs\|candidates\|compose\|notify\|seed-demo\|admin\|resumes\|health)'
NEW_LINE = r'location ~ ^/api/(screen|parse|jobs|candidates|compose|notify|seed-demo|admin|resumes|health|profile|jd|boolean-search|import|integrations|comm|audit|webhooks)(/.*)?$'

# Use sed to do the replacement
cmd = (r"sed -i 's|location ~ \^/api/(screen|parse|jobs|candidates|compose|notify|seed-demo|admin|resumes|health)(/.*).*\$|" +
       NEW_LINE + r"|g' /etc/nginx/sites-enabled/recruit.srpailabs.com")

# More reliable: use Python to write a corrected file
_,s,e = client.exec_command('cat /etc/nginx/sites-enabled/recruit.srpailabs.com')
content = s.read().decode()

old_route = 'location ~ ^/api/(screen|parse|jobs|candidates|compose|notify|seed-demo|admin|resumes|health)(/.*)?$ {'
new_route = 'location ~ ^/api/(screen|parse|jobs|candidates|compose|notify|seed-demo|admin|resumes|health|profile|jd|boolean-search|import|integrations|comm|audit|webhooks)(/.*)?$ {'

if old_route in content:
    content = content.replace(old_route, new_route)
    # Write back
    sftp = client.open_sftp()
    with sftp.open('/etc/nginx/sites-enabled/recruit.srpailabs.com', 'w') as f:
        f.write(content)
    sftp.close()
    print('Updated nginx config')
    # Test + reload
    _,s,e = client.exec_command('nginx -t && systemctl reload nginx && echo RELOAD_OK')
    out = s.read().decode() + e.read().decode()
    print(out)
else:
    print('Old route not found! Current content:')
    print(content[:300])

client.close()
