import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

# Get the COMPLETE nginx config
_, stdout, stderr = client.exec_command("cat /etc/nginx/sites-enabled/recruit.srpailabs.com", timeout=30)
out = stdout.read().decode().strip()
print(out)
client.close()
