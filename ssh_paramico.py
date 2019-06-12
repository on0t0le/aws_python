import paramiko

host_address = '52.59.152.156'

k = paramiko.RSAKey.from_private_key_file("D:\\Downloads\\aperture-web1.pem")
c = paramiko.SSHClient()
c.set_missing_host_key_policy(paramiko.AutoAddPolicy())
print("connecting")
c.connect(hostname=host_address, username="ec2-user", pkey=k)
print("connected")
commands = ["ls /home/", "ls /tmp", "sudo -S mkdir /tmp/test"]
for command in commands:
    #print("Executing {}".format(command))
    stdin, stdout, stderr = c.exec_command(command)
    print(stdout.read())
    print("Errors")
    print(stderr.read())
# stdin, stdout, stderr = c.exec_command('sudo -S whoami')
# print(stdout.read())
c.close()
