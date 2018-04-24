import core.plugin
import core.cidr

import socket
import os
import multiprocessing
import threading
import time

# needed for pickling reasons
def work_function(remote, ip):
    remote.run_ip_thread(ip)

class Remote(core.plugin.Plugin):
    def __init__(self, shell):
        super(Remote, self).__init__(shell)

        self.local = None
        self.assignments = {}

    def load(self):
        super(Remote, self).load()

        self.options.register("RHOSTS", "", "the hosts to target (or a file)", required=True)
        self.options.register("RPORT", "", "the port to target", required=True)
        self.options.register("THREADS", "5", "number of worker threads")

    def run(self):
        rhosts = self.options.get("RHOSTS")

        try:
            rport = int(self.options.get("RPORT"))
        except:
            self.shell.print_warning("Invalid RPORT value!")
            return

        thread_count = int(self.options.get("THREADS"))

        if os.path.isfile(rhosts):
            rhosts = open(rhosts, "rb").read()

        # enhanced cool threaded version
        threads = []
        try:
            for i in range(0, thread_count):
                threads.append(None)

            for ip in core.cidr.get_ips(rhosts):
                waiting = True
                while waiting:
                    for i in range(0, thread_count):
                        t = threads[i]
                        if t == None or not t.is_alive():
                            waiting = False
                            threads[i] = threading.Thread(target=work_function, args=(self, ip))
                            threads[i].daemon = True
                            threads[i].start()
                            break

        except KeyboardInterrupt:
            pass

        for t in threads:
            if t is not None:
                t.join()

        '''
        pool = multiprocessing.Pool(processes=threads)

        for ip in core.cidr.get_ips(rhosts):
            self.shell.print_status("Applying async to %s" % ip)
            pool.apply_async(work_function, args=(self, ip))

        '''

        # shitty single threaded noob way
        #for ip in ips:
            #self.run_ip(ip, rport)

    def run_ip_thread(self, ip):
        rport = self.options.get("RPORT")
        #self.local = threading.local()
        #self.local.ip = ip
        #self.local.port = self.options.get("RPORT")

        #self.local.__setattr__('ip', ip)
        #self.local.__setattr__('port', self.options.get("RPORT"))

        # thread locals were sometimes not being assigned so just use a tid map
        tid = threading.current_thread().ident
        self.assignments[tid] = "%s:%s" % (ip, rport)

        self.print_status("Worker %s spawned." % threading.current_thread().getName())

        try:
            self.run_ip(ip, rport)
        except socket.error as serr:
            self.print_error(serr.strerror)
        except:
            raise
        finally:
            self.assignments.pop(threading.current_thread().ident, None)

    def print_status(self, message):
        self.shell.print_status(self.add_print_preamble(message))

    def print_good(self, message):
        self.shell.print_good(self.add_print_preamble(message))

    def print_error(self, message):
        self.shell.print_error(self.add_print_preamble(message))

    def print_warning(self, message):
        self.shell.print_warning(self.add_print_preamble(message))

    def add_print_preamble(self, message):
        #if self.local is not None:
            #return "%s:%s\t- %s" % (self.local.ip, self.local.port, message)
        tid = threading.current_thread().ident
        if tid in self.assignments:
            return "%s\t- %s" % (self.assignments[tid], message)

        return message

    def run_ip(self, ip, port):
        pass
