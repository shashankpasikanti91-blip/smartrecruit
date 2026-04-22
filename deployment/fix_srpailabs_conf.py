import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

FIXED_CONF = """\
server {
    listen 80;
    server_name srpailabs.com www.srpailabs.com
                autonomous.srpailabs.com app.srpailabs.com
                mediflow.srpailabs.com
                growth.srpailabs.com;
    return 301 https://$host$request_uri;
}
server {
    listen 443 ssl http2;
    server_name srpailabs.com www.srpailabs.com;
    ssl_certificate     /etc/letsencrypt/live/srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srpailabs.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
    root /var/www/srpailabs/dist;
    index index.html;
    # HTML - NEVER cache so new deploys take effect immediately
    location / {
        add_header Cache-Control "no-cache, no-store, must-revalidate" always;
        add_header Pragma "no-cache" always;
        add_header Expires "0" always;
        try_files $uri $uri/ /index.html;
    }
    # Hashed assets - cache forever (hash changes on rebuild)
    location /assets/ {
        add_header Cache-Control "public, max-age=31536000, immutable" always;
        try_files $uri =404;
    }
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    if ($host = www.srpailabs.com) {
        return 301 https://srpailabs.com$request_uri;
    }
}
server {
    listen 443 ssl http2;
    server_name autonomous.srpailabs.com;
    ssl_certificate     /etc/letsencrypt/live/srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srpailabs.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
    location / {
        proxy_pass http://127.0.0.1:3001;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
server {
    listen 443 ssl http2;
    server_name app.srpailabs.com;
    ssl_certificate     /etc/letsencrypt/live/srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srpailabs.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
    location / {
        proxy_pass http://127.0.0.1:3002;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
server {
    listen 443 ssl http2;
    server_name mediflow.srpailabs.com;
    ssl_certificate     /etc/letsencrypt/live/srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srpailabs.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
    location / {
        proxy_pass http://127.0.0.1:3003;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
server {
    listen 443 ssl http2;
    server_name growth.srpailabs.com;
    ssl_certificate     /etc/letsencrypt/live/srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/srpailabs.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;
    location / {
        proxy_pass http://127.0.0.1:3005;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
"""

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

# Write the fixed srpailabs.conf
sftp = client.open_sftp()
with sftp.open('/etc/nginx/sites-enabled/srpailabs.conf', 'w') as f:
    f.write(FIXED_CONF)
sftp.close()
print("srpailabs.conf written (recruit.srpailabs.com duplicate removed)")

# Test and reload nginx
for label, cmd in [
    ("nginx test", "nginx -t 2>&1"),
    ("reload nginx", "systemctl reload nginx && echo 'nginx reloaded OK'"),
    ("test /app redirect", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/app"),
    ("test /dashboard", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/dashboard"),
    ("test /api/jd", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/jd"),
    ("test /api/candidates", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/api/candidates"),
    ("test /login", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/login"),
    ("FastAPI health", "curl -sf http://127.0.0.1:8009/health"),
    ("NextJS health", "curl -sf http://127.0.0.1:3010/api/health"),
]:
    _, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n[{label}]  {out or err or '(empty)'}")

client.close()
print("\n=== All done ===")
