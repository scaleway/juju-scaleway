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

import os

from juju_scaleway.exceptions import ProviderAPIError

import json
import requests


class Entity(object):

    @classmethod
    def from_dict(cls, data):
        i = cls()
        i.__dict__.update(data)
        return i


class Server(Entity):
    """
    Attributes: id, name, image, state, public_ip, creation_date
    """


class Image(Entity):
    """
    Attributes:, id, name, arch, public
    """


class Client(object):

    def __init__(self, access_key, secret_key):
        self.access_key = access_key
        self.secret_key = secret_key
        self.api_url_base = 'https://api.scaleway.com'

    def get_images(self):
        data = self.request("/images")
        return [Image.from_dict(image) for image in data.get("images", [])]

    def get_url(self, target):
        return "%s%s" % (self.api_url_base, target)

    def get_servers(self):
        data = self.request("/servers")
        return [Server.from_dict(server) for server in data.get('servers', [])]

    def get_server(self, server_id):
        data = self.request("/servers/%s" % (server_id))
        return Server.from_dict(data.get('server', {}))

    def create_server(self, name, image):
        params = dict(
            name=name,
            image=image,
            organization=self.access_key)

        data = self.request('/servers', method='POST', params=params)
        server = Server.from_dict(data.get('server', {}))
        # Execute poweron action
        self.request('/servers/%s/action' % (server.id),
                     method='POST', params={'action': 'poweron'})

        return server

    def destroy_server(self, server_id):
        data = self.request('/servers/%s/action' % (server_id),
                            method='POST', params={'action': 'terminate'})
        return data.get('task')

    def request(self, target, method='GET', params=None):
        params = params and dict(params) or {}

        headers = {'User-Agent': 'juju/client'}
        headers = {'X-Auth-Token': self.secret_key}
        url = self.get_url(target)

        if method == 'POST':
            headers['Content-Type'] = "application/json"
            response = requests.post(
                url, headers=headers, data=json.dumps(params)
            )
        else:
            response = requests.get(url, headers=headers, params=params)

        data = response.json()
        if not data:
            raise ProviderAPIError(response, 'No json result found')
        if response.status_code >= 400:
            raise ProviderAPIError(response, data['message'])

        return data

    @classmethod
    def connect(cls):
        access_key = os.environ.get('SCALEWAY_ACCESS_KEY')
        secret_key = os.environ.get('SCALEWAY_SECRET_KEY')
        if not access_key or not secret_key:
            raise KeyError("Missing api credentials")
        return cls(access_key, secret_key)


def main():
    import code
    client = Client.connect()
    code.interact(local={'client': client})


if __name__ == '__main__':
    main()
