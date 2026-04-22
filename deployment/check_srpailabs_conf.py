import paramiko

HOST = "5.223.67.236"
USER = "root"
PASS = "856Reey@nsh"

client = paramiko.SSHClient()
client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
client.connect(HOST, username=USER, password=PASS, timeout=30)

# Get the relevant part of srpailabs.conf
_, stdout, stderr = client.exec_command("cat /etc/nginx/sites-enabled/srpailabs.conf", timeout=15)
out = stdout.read().decode().strip()
print(out[:4000])
client.close()
