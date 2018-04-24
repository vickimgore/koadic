import core.remote
import core.smbclient
import string

class PSExec(core.remote.Remote):
    def __init__(self, shell):
        super(PSExec, self).__init__(shell)

    def load(self):
        super(PSExec, self).load()
        self.options.set("RPORT", "445")#, "default port")
        self.options.register("SMBDOMAIN", ".", "domain to authenticate against", required=False)
        self.options.register("SMBUSER", "", "user account to login with", required=False)
        self.options.register("SMBPASS", "", "cleartext password or NTLM hash", required=False)
        self.options.register("TIMEOUT", "3", "how long blocking sockets will last")
        self.options.register("SHARE", "C$", "the writeable share to use", required=False)
        self.options.register("RPATH", "", "the file path to use on the share")

    def run_ip(self, ip, port):
        timeout = float(self.options.get("TIMEOUT"))
        user = self.options.get("SMBUSER")
        domain = self.options.get("SMBDOMAIN")
        password = self.options.get("SMBPASS")

        client = core.smbclient.SMBClient(self, ip, timeout=timeout)

        # figure out if this is an NTLM hash
        nthash = password.split(":")[1] if ":" in password else password
        nthash = nthash.strip().lower()

        if len(nthash) == 32 and all(c in string.hexdigits for c in nthash):
            client.login(user, password, domain=domain, nthash=password)
        else:
            client.login(user, password, domain=domain)

        server_os = client.get_server_os()
        self.print_status('Login success - Target OS: %s' % server_os)

        self.smb_pwn(client, ip, port)

    	client.disconnect_tree(client.get_tid())
    	client.logoff()
    	client.get_socket().close()


    def smb_pwn(self, client, ip, port):
        pass
        #print(client)
