import logging
import time
import subprocess

from juju_scaleway.exceptions import TimeoutError
from juju_scaleway import ssh

log = logging.getLogger("juju.scaleway")


class MachineOp(object):

    def __init__(self, provider, env, params, **options):
        self.provider = provider
        self.env = env
        self.params = params
        self.created = time.time()
        self.options = options

    def run(self):
        raise NotImplementedError()


class MachineAdd(MachineOp):

    timeout = 360
    delay = 8

    def run(self):
        server = self.provider.launch_server(self.params)
        self.provider.wait_on(server)
        server = self.provider.get_server(server.id)
        self.verify_ssh(server)
        return server

    def verify_ssh(self, server):
        """Workaround for manual provisioning and ssh availability.
        Manual provider bails immediately upon failure to connect on
        ssh, we loop to allow the server time to start ssh.
        """
        max_time = self.timeout + time.time()
        running = False
        while max_time > time.time():
            try:
                if ssh.check_ssh(server.public_ip['address']):
                    running = True
                    break
            except subprocess.CalledProcessError as e:
                if ("Connection refused" in e.output or
                        "Connection timed out" in e.output or
                        "Connection closed" in e.output or
                        "Connection reset by peer" in e.output):
                    log.debug(
                        "Waiting for ssh on id:%s ip:%s name:%s remaining:%d",
                        server.id, server.public_ip['address'], server.name,
                        int(max_time-time.time()))
                    time.sleep(self.delay)
                else:
                    log.error(
                        "Could not ssh to server name: %s id: %s ip: %s\n%s",
                        server.name, server.id, server.public_ip['address'],
                        e.output)
                    raise

        if running is False:
            raise TimeoutError(
                "Could not provision id:%s name:%s ip:%s before timeout" % (
                    server.id, server.name, server.public_ip['address']))


class MachineRegister(MachineAdd):

    def run(self):
        server = super(MachineRegister, self).run()
        try:
            machine_id = self.env.add_machine(
                "ssh:root@%s" % server.public_ip['address'],
                key=self.options.get('key'))
        except:
            self.provider.terminate_server(server.id)
            raise
        return server, machine_id


class MachineDestroy(MachineOp):

    def run(self):
        if not self.options.get('iaas_only'):
            self.env.terminate_machines([self.params['machine_id']])
        if self.options.get('env_only'):
            return
        log.debug("Destroying server %s", self.params['server_id'])
        self.provider.terminate_server(self.params['server_id'])
