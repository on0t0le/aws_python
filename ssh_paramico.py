import paramiko

host_address = '52.59.198.217'

k = paramiko.RSAKey.from_private_key_file("./testkeypy")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("connecting")
c.connect(hostname=host_address, username="ec2-user", pkey=k)
print("connected")
commands = ["sudo -S mkfs.xfs -f /dev/xvdh", "sudo -S mkdir /data", "sudo -S mount /dev/xvdh /data"]
for command in commands:
    print("Executing {}".format(command))
    stdin, stdout, stderr = c.exec_command(command)
    print(stdout.read())
    print("Errors")
    print(stderr.read())
# stdin, stdout, stderr = c.exec_command('sudo -s mkfs.xfs -f /dev/xvdh')
# print(stdout.read())
c.close()
