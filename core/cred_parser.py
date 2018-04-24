import collections
import tabulate
import traceback

class CredParse(object):

    '''
        shell - the koadic superobject
        printer - an object with standard shell-like print_status functions
        ip - the ip the creds were scraped from
        domain - the session computer
    '''
    def __init__(self, shell, printer, ip, domain):
        self.shell = shell
        self.printer = printer
        self.ip = ip
        self.domain = domain

    def new_cred(self):
        cred = {}
        cred["IP"] = ""
        cred["Domain"] = ""
        cred["Username"] = ""
        cred["Password"] = ""
        cred["NTLM"] = ""
        cred["SHA1"] = ""
        cred["DCC"] = ""
        cred["DPAPI"] = ""
        cred["LM"] = ""
        cred["Extra"] = {}
        cred["Extra"]["Password"] = []
        cred["Extra"]["NTLM"] = []
        cred["Extra"]["SHA1"] = []
        cred["Extra"]["DCC"] = []
        cred["Extra"]["DPAPI"] = []
        cred["Extra"]["LM"] = []
        return cred

    def parse_hashdump_sam(self, data):

        output = data

        sam_sec1 = output.split("[*] Dumping local SAM hashes (uid:rid:lmhash:nthash)\n")[1]
        sam_sec2 = sam_sec1.split("[*] Dumping cached domain logon information (uid:encryptedHash:longDomain:domain)")[0]
        sam_sec = sam_sec2.splitlines()
        cached_sec1 = output.split("[*] Dumping cached domain logon information (uid:encryptedHash:longDomain:domain)\n")[1]
        cached_sec2 = cached_sec1.split("[*] Dumping LSA Secrets")[0]
        cached_sec = cached_sec2.splitlines()

        for htype in ["sam", "cached"]:
            hsec = locals().get(htype+"_sec")
            if hsec and hsec[0].split()[0] == "[-]":
                continue
            for h in hsec:
                c = self.new_cred()
                c["IP"] = self.ip#self.session.ip
                hparts = h.split(":")
                c["Username"] = hparts[0]
                if htype == "sam":
                    c["NTLM"] = hparts[3]
                    c["Domain"] = self.domain# self.session.computer
                else:
                    c["DCC"] = hparts[1]
                    c["Domain"] = hparts[3]

                key = tuple([c["Domain"].lower(), c["Username"].lower()])
                if key in self.shell.creds_keys:
                    if not self.shell.creds[key]["NTLM"] and c["NTLM"]:
                        self.shell.creds[key]["NTLM"] = c["NTLM"]
                    elif self.shell.creds[key]["NTLM"] != c["NTLM"] and c["NTLM"]:
                        self.shell.creds[key]["Extra"]["NTLM"].append(c["NTLM"])

                    if not self.shell.creds[key]["DCC"] and c["DCC"]:
                        self.shell.creds[key]["DCC"] = c["DCC"]
                    elif self.shell.creds[key]["DCC"] != c["DCC"] and c["DCC"]:
                        self.shell.creds[key]["Extra"]["DCC"].append(c["DCC"])
                else:
                    self.shell.creds_keys.append(key)
                    self.shell.creds[key] = c

        return

    def parse_mimikatz(self, data, returnearly=True):
        parsed_data = ""
        data = data.replace("\r", "")
        # data = data.split("mimikatz(")[1]
        if "token::elevate" in data and "Impersonated !" in data:
            self.printer.print_good("token::elevate -> got SYSTEM!")
            if returnearly:
                return

        if "privilege::debug" in data and "OK" in data:
            self.printer.print_good("privilege::debug -> got SeDebugPrivilege!")
            if returnearly:
                return

        if "ERROR kuhl_m_" in data:
            self.printer.error("0", data.split("; ")[1].split(" (")[0], "Error", data)
            self.printer.errstat = 1
            if returnearly:
                return

        try:
            # print("UHHH HELOOOOOOOOOOOOOOOOOOO")
            if "Authentication Id :" in data and ("sekurlsa::logonpasswords" in data.lower()
                    or "sekurlsa::msv" in data.lower()
                    or "sekurlsa::tspkg" in data.lower()
                    or "sekurlsa::wdigest" in data.lower()
                    or "sekurlsa::kerberos" in data.lower()
                    or "sekurlsa::ssp" in data.lower()
                    or "sekurlsa::credman" in data.lower()):
                # print(data)
                from tabulate import tabulate
                nice_data = data.split('\n\n')
                cred_headers = ["msv","tspkg","wdigest","kerberos","ssp","credman"]
                msv_all = []
                tspkg_all = []
                wdigest_all = []
                kerberos_all = []
                ssp_all = []
                credman_all = []
                #print(nice_data)
                for section in nice_data:
                    if 'Authentication Id' in section:
                        msv = collections.OrderedDict()
                        tspkg = collections.OrderedDict()
                        wdigest = collections.OrderedDict()
                        kerberos = collections.OrderedDict()
                        ssp = collections.OrderedDict()
                        credman = collections.OrderedDict()

                        for index, cred_header in enumerate(cred_headers):
                            cred_dict = locals().get(cred_header)
                            try:
                                cred_sec1 = section.split(cred_header+" :\t")[1]
                            except:
                                continue
                            if index < len(cred_headers)-1:
                                cred_sec = cred_sec1.split("\t"+cred_headers[index+1]+" :")[0].splitlines()
                            else:
                                cred_sec = cred_sec1.splitlines()

                            for line in cred_sec:
                                if '\t *' in line:
                                    cred_dict[line.split("* ")[1].split(":")[0].rstrip()] = line.split(": ")[1].split("\n")[0]
                            if cred_dict:
                                cred_list = locals().get(cred_header+"_all")
                                cred_list.append(cred_dict)

                for cred_header in cred_headers:
                    cred_list = locals().get(cred_header+"_all")
                    tmp = [collections.OrderedDict(t) for t in set([tuple(d.items()) for d in cred_list])]
                    del cred_list[:]
                    cred_list.extend(tmp)

                parsed_data += "Results\n\n"

                for cred_header in cred_headers:
                    banner = cred_header+" credentials\n"+(len(cred_header)+12)*"="+"\n\n"
                    cred_dict = locals().get(cred_header+"_all")
                    if not cred_dict:
                        continue
                    cred_dict = sorted(cred_dict, key=lambda k: k['Username'])
                    ckeys = []
                    [[ckeys.append(k) for k in row if k not in ckeys] for row in cred_dict]
                    for cred in cred_dict:
                        key = tuple([cred["Domain"].lower(), cred["Username"].lower()])
                        if key not in self.shell.creds_keys:
                            self.shell.creds_keys.append(key)
                            c = self.new_cred()
                            c["IP"] = self.ip#self.session.ip
                            for subkey in cred:
                                c[subkey] = cred[subkey]
                            if "\\" in c["Username"]:
                                c["Username"] = c["Username"].split("\\")[1]
                            if "\\" in c["Domain"]:
                                c["Domain"] = c["Domain"].split("\\")[0]
                            if c["Password"] == "(null)":
                                c["Password"] = ""
                            self.shell.creds[key] = c

                        else:
                            if "Password" in cred:
                                cpass = cred["Password"]
                                if not self.shell.creds[key]["Password"] and cpass != "(null)" and cpass:
                                    self.shell.creds[key]["Password"] = cpass
                                elif self.shell.creds[key]["Password"] != cpass and cpass != "(null)" and cpass:
                                    self.shell.creds[key]["Extra"]["Password"].append(cpass)

                            if "NTLM" in cred:
                                cntlm = cred["NTLM"]
                                if not self.shell.creds[key]["NTLM"]:
                                    self.shell.creds[key]["NTLM"] = cntlm
                                elif self.shell.creds[key]["NTLM"] != cntlm and cntlm:
                                    self.shell.creds[key]["Extra"]["NTLM"].append(cntlm)

                            if "SHA1" in cred:
                                csha1 = cred["SHA1"]
                                if not self.shell.creds[key]["SHA1"]:
                                    self.shell.creds[key]["SHA1"] = csha1
                                elif self.shell.creds[key]["SHA1"] != csha1 and csha1:
                                    self.shell.creds[key]["Extra"]["SHA1"].append(csha1)

                            if "DPAPI" in cred:
                                cdpapi = cred["DPAPI"]
                                if not self.shell.creds[key]["DPAPI"]:
                                    self.shell.creds[key]["DPAPI"] = cdpapi
                                elif self.shell.creds[key]["DPAPI"] != cdpapi and cdpapi:
                                    self.shell.creds[key]["Extra"]["DPAPI"].append(cdpapi)

                    separators = collections.OrderedDict([(k, "-"*len(k)) for k in ckeys])
                    cred_dict = [separators] + cred_dict
                    parsed_data += banner
                    parsed_data += tabulate(cred_dict, headers="keys", tablefmt="plain")
                    parsed_data += "\n\n"

                # data = parsed_data

            if "SAMKey :" in data and "lsadump::sam" in data.lower():
                domain = data.split("Domain : ")[1].split("\n")[0]
                sam_parsed_data = data.split("\n\n")
                for section in sam_parsed_data:
                    if "RID  :" in section:
                        c = self.new_cred()
                        c["IP"] = self.ip#self.session.ip
                        c["Username"] = section.split("User : ")[1].split("\n")[0]
                        c["Domain"] = domain
                        lm = section.split("LM   : ")[1].split("\n")[0]
                        ntlm = section.split("NTLM : ")[1].split("\n")[0]
                        key = tuple([c["Domain"].lower(), c["Username"].lower()])
                        if key not in self.shell.creds_keys:
                            self.shell.creds_keys.append(key)
                            c["NTLM"] = ntlm
                            c["LM"] = lm
                            self.shell.creds[key] = c
                        else:
                            if not self.shell.creds[key]["NTLM"] and ntlm:
                                self.shell.creds[key]["NTLM"] = ntlm
                            elif self.shell.creds[key]["NTLM"] != ntlm and ntlm:
                                self.shell.creds[key]["Extra"]["NTLM"].append(ntlm)

                            if not self.shell.creds[key]["LM"] and lm:
                                self.shell.creds[key]["LM"] = lm
                            elif self.shell.creds[key]["LM"] != lm and lm:
                                self.shell.creds[key]["Extra"]["LM"].append(lm)

            return parsed_data
        except Exception as e:
            data += "\n\n\n"
            data += traceback.format_exc()
            return data
