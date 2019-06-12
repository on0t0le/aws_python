from paramiko import RSAKey


filename = 'mytestkey'

# generating private key
prv = RSAKey.generate(bits=2048)
prv.write_private_key_file(filename)

# generating public key
pub = RSAKey(filename=filename)
with open("%s.pub" % filename, "w") as f:
    f.write("%s %s" % (pub.get_name(), pub.get_base64()))