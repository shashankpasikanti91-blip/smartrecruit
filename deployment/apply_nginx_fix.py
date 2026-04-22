import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

NGINX_CONF = "/etc/nginx/sites-available/recruit.srpailabs.com"

# The updated nginx config with /app → redirect to /dashboard
NEW_CONFIG = r"""# SRP SmartRecruit - recruit.srpailabs.com
# Next.js Auth frontend on :3010, FastAPI ATS backend on :8009

limit_req_zone $binary_remote_addr zone=ats_api:10m rate=10r/s;
limit_req_zone $binary_remote_addr zone=ats_auth:10m rate=3r/s;

server {
    listen 80;
    listen [::]:80;
    server_name recruit.srpailabs.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name recruit.srpailabs.com;

    ssl_certificate     /etc/letsencrypt/live/recruit.srpailabs.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/recruit.srpailabs.com/privkey.pem;
    include             /etc/letsencrypt/options-ssl-nginx.conf;
    ssl_dhparam         /etc/letsencrypt/ssl-dhparams.pem;

    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;
    add_header Permissions-Policy "camera=(), microphone=(), geolocation=()" always;
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    client_max_body_size 15M;

    # -- NextAuth (Google OAuth) --> Next.js :3010
    # MUST appear before the general /api/ block (regex beats prefix in nginx)
    location ~ ^/api/auth/(providers|session|csrf|callback|signin|signout|error)(/.*)?$ {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 30s;
    }

    # -- Next.js API routes (screen, parse, jobs, candidates, compose, etc.) --
    # These must appear BEFORE the general /api/ catch-all
    location ~ ^/api/(screen|parse|jobs|candidates|compose|notify|seed-demo|admin|resumes|health|profile|jd|boolean-search|import|integrations|comm|audit|webhooks)(/.*)?$ {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 180s;
        proxy_connect_timeout 15s;
        client_max_body_size 15M;
    }

    # -- FastAPI auth endpoints (login, register, verify-otp, forgot-password) --
    location /api/auth/ {
        limit_req zone=ats_auth burst=5 nodelay;
        limit_req_status 429;
        proxy_pass http://127.0.0.1:8009;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # -- FastAPI Backend (ATS API) --
    location /api/ {
        limit_req zone=ats_api burst=20 nodelay;
        proxy_pass http://127.0.0.1:8009;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
        proxy_connect_timeout 10s;
    }

    location /health {
        proxy_pass http://127.0.0.1:8009;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # /app used to serve the old Jinja2 dashboard -- redirect to Next.js now
    location = /app {
        return 301 /dashboard;
    }

    location /static/ {
        proxy_pass http://127.0.0.1:8009;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        expires 7d;
        add_header Cache-Control "public, immutable";
    }

    # -- Next.js static assets --
    location /_next/static/ {
        proxy_pass http://127.0.0.1:3010;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }

    # -- Next.js pages (login, signup, dashboard, etc.) --
    location / {
        proxy_pass http://127.0.0.1:3010;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
        proxy_read_timeout 120s;
        proxy_connect_timeout 15s;
    }

    # -- Block hidden files --
    location ~ /\. {
        deny all;
    }
}
"""

# Write the new config
sftp = client.open_sftp()
with sftp.open(NGINX_CONF, 'w') as f:
    f.write(NEW_CONFIG)
sftp.close()
print("Config written.")

# Test and reload nginx
for label, cmd in [
    ("nginx test", "nginx -t 2>&1"),
    ("reload nginx", "systemctl reload nginx && echo 'nginx reloaded'"),
    ("test /app redirect", "curl -sk -o /dev/null -w 'HTTP %{http_code} -> Location: %{redirect_url}' https://recruit.srpailabs.com/app"),
    ("test /dashboard", "curl -sk -o /dev/null -w 'HTTP %{http_code}' https://recruit.srpailabs.com/dashboard"),
]:
    _, stdout, stderr = client.exec_command(cmd, timeout=20)
    out = stdout.read().decode().strip()
    err = stderr.read().decode().strip()
    print(f"\n[{label}]")
    print(out or err or "(empty)")

client.close()
print("\nDone.")
