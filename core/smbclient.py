import os
import sys
import socket
import time
import random
import uuid
import argparse
import StringIO
from impacket import smb, smbconnection
from impacket.dcerpc.v5 import transport

class SMBClient(smb.SMB):
    def __init__(self, printer, remote_host, timeout=3):
        self._smbConn = None
        self.printer = printer
        smb.SMB.__init__(self, remote_host, remote_host, timeout=timeout)

    def get_smbconnection(self):
        if self._smbConn is None:
            self.smbConn = smbconnection.SMBConnection(self.get_remote_host(), self.get_remote_host(), existingConnection=self, manualNegotiate=True)
        return self.smbConn

    def get_dce_rpc(self, named_pipe):
        smbConn = self.get_smbconnection()
        rpctransport = transport.SMBTransport(self.get_remote_host(), self.get_remote_host(), filename='\\'+named_pipe, smb_connection=smbConn)
        return rpctransport.get_dce_rpc()

    def service_exec(self, cmd):
        import random
        import string
        from impacket.dcerpc.v5 import transport, srvs, scmr
        conn = self

        service_name = ''.join([random.choice(string.letters) for i in range(4)])

        # Setup up a DCE SMBTransport with the connection already in place

        #rpctransport = transport.SMBTransport(conn.get_remote_host(), conn.get_remote_host(), filename='\\svcctl', smb_connection=conn)
        #rpcsvc = rpctransport.get_dce_rpc()

        rpcsvc = conn.get_dce_rpc('svcctl')
        rpcsvc.connect()
        rpcsvc.bind(scmr.MSRPC_UUID_SCMR)
        svcHandle = None
        try:
            self.printer.print_status("Opening SVCManager on %s....." % conn.get_remote_host())
            resp = scmr.hROpenSCManagerW(rpcsvc)
            svcHandle = resp['lpScHandle']

            # First we try to open the service in case it exists. If it does, we remove it.
            try:
                resp = scmr.hROpenServiceW(rpcsvc, svcHandle, service_name+'\x00')
            except Exception as e:
                if str(e).find('ERROR_SERVICE_DOES_NOT_EXIST') == -1:
                    raise e  # Unexpected error
            else:
                # It exists, remove it
                scmr.hRDeleteService(rpcsvc, resp['lpServiceHandle'])
                scmr.hRCloseServiceHandle(rpcsvc, resp['lpServiceHandle'])

            self.printer.print_status('Creating service %s.....' % service_name)
            resp = scmr.hRCreateServiceW(rpcsvc, svcHandle, service_name + '\x00', service_name + '\x00', lpBinaryPathName=cmd + '\x00')
            serviceHandle = resp['lpServiceHandle']

            if serviceHandle:
                # Start service
                try:
                    self.printer.print_status('Starting service %s.....' % service_name)
                    scmr.hRStartServiceW(rpcsvc, serviceHandle)
                    # is it really need to stop?
                    # using command line always makes starting service fail because SetServiceStatus() does not get called
                    #print('Stoping service %s.....' % service_name)
                    #scmr.hRControlService(rpcsvc, serviceHandle, scmr.SERVICE_CONTROL_STOP)
                except Exception as e:
                    self.printer.print_warning(str(e))

                print('Removing service %s.....' % service_name)
                scmr.hRDeleteService(rpcsvc, serviceHandle)
                scmr.hRCloseServiceHandle(rpcsvc, serviceHandle)
        except Exception as e:
            self.printer.print_error("ServiceExec Error on: %s" % conn.get_remote_host())
            self.printer.print_error(str(e))
        finally:
            if svcHandle:
                scmr.hRCloseServiceHandle(rpcsvc, svcHandle)

        rpcsvc.disconnect()

    def upload_file(self, share, fname, localfile):
        smbConn = self.get_smbconnection()
        with open(localfile, 'rb') as fp:
            smbConn.putFile(share, fname, fp.read)

    def download_file(self, share, fname):
        smbConn = self.get_smbconnection()
        output = StringIO.StringIO()
        smbConn.getFile(share, fname, output.write)
        out = output.getvalue()
        output.close()
        return out

    def delete_file(self, share, fname):
        smbConn = self.get_smbconnection()
        smbConn.deleteFile(share, fname)
