import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

# Get the current (broken) srpailabs.conf
_, stdout, _ = client.exec_command("cat /etc/nginx/sites-enabled/srpailabs.conf", timeout=15)
content = stdout.read().decode()
print(content)
client.close()
