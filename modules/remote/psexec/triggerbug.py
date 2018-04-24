import core.remote

class TriggerBug(core.remote.Remote):

    NAME = "TriggerBug"
    DESCRIPTION = "Triggers print bug"
    AUTHORS = ['zerosum0x0', 'TheNaterz']

    def load(self):
        super(TriggerBug, self).load()
        self.options.set("RHOSTS", "192.168.90.0/24")
        self.options.set("RPORT", "123")

    def run_ip(self, ip, rport):
        self.print_status("Triggering bug!")
