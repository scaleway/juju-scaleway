# -*- coding: utf-8 -*-
#
# Copyright (c) 2014-2015 Online SAS and Contributors. All Rights Reserved.
#                         Edouard Bonlieu <ebonlieu@scaleway.com>
#                         Julien Castets <jcastets@scaleway.com>
#                         Manfred Touron <mtouron@scaleway.com>
#                         Kevin Deldycke <kdeldycke@scaleway.com>
#
# Licensed under the BSD 2-Clause License (the "License"); you may not use this
# file except in compliance with the License. You may obtain a copy of the
# License at http://opensource.org/licenses/BSD-2-Clause

import logging
import os
import time
import itertools

from juju_scaleway.exceptions import ConfigError, ProviderError
from juju_scaleway.client import Client

logger = logging.getLogger("juju.scaleway")


def factory():
    cfg = Scaleway.get_config()
    return Scaleway(cfg)


def validate():
    Scaleway.get_config()


class Scaleway(object):

    def __init__(self, config, client=None):
        self.config = config
        if client is None:
            self.client = Client(
                config['access_key'],
                config['secret_key'])

    @classmethod
    def get_config(cls):
        provider_conf = {}

        access_key = os.environ.get('SCALEWAY_ACCESS_KEY')
        if access_key:
            provider_conf['access_key'] = access_key

        secret_key = os.environ.get('SCALEWAY_SECRET_KEY')
        if secret_key:
            provider_conf['secret_key'] = secret_key

        if 'access_key' not in provider_conf or \
           'secret_key' not in provider_conf:
            raise ConfigError("Missing Scaleway api credentials")
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
        print(server.name)
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
                logger.debug(
                    "Waiting for server:%s ip:%s waited:%ds",
                    server.name,
                    server.public_ip['address'] if server.public_ip else None,
                    count * delay
                )
            time.sleep(delay)
