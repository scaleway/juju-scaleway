import logging
import os
import time
import itertools

from juju_onlinelabs.exceptions import ConfigError, ProviderError
from juju_onlinelabs.client import Client

log = logging.getLogger("juju.onlinelabs")


def factory():
    cfg = OnlineLabs.get_config()
    return OnlineLabs(cfg)


def validate():
    OnlineLabs.get_config()


class OnlineLabs(object):

    def __init__(self, config, client=None):
        self.config = config
        if client is None:
            self.client = Client(
                config['access_key'],
                config['secret_key'])

    @classmethod
    def get_config(cls):
        provider_conf = {}

        access_key = os.environ.get('ONLINELABS_ACCESS_KEY')
        if access_key:
            provider_conf['access_key'] = access_key

        secret_key = os.environ.get('ONLINELABS_SECRET_KEY')
        if secret_key:
            provider_conf['secret_key'] = secret_key

        if (not 'access_key' in provider_conf or
                not 'secret_key' in provider_conf):
            raise ConfigError("Missing Online Labs api credentials")
        return provider_conf

    def get_servers(self):
        return self.client.get_servers()

    def get_server(self, server_id):
        return self.client.get_server(server_id)

    def launch_server(self, params):
        return self.client.create_server(**params)

    def terminate_server(self, server_id):
        self.client.destroy_server(server_id)

    def wait_on(self, server):
      # Wait up to 5 minutes, in 30 sec increments
        print server.name
        result = self._wait_on_server(server, 30, 10)
        if not result:
            raise ProviderError("Could not provision server before timeout")
        return result

    def _wait_on_server(self, server, limit, delay=10):
        # Redo cci.wait to give user feedback in verbose mode.
        for count, new_server in enumerate(itertools.repeat(server.id)):
            server = self.get_server(new_server)
            if server.state == 'running':
                return True
            if count >= limit:
                return False
            if count and count % 3 == 0:
                log.debug("Waiting for server:%s ip:%s waited:%ds" % (
                    server.name, server.public_ip['address'] if server.public_ip else None, count*delay))
            time.sleep(delay)

