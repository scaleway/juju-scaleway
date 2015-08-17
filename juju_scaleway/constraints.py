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

SERIES_MAP = {
    'Ubuntu Utopic (14.10)': 'utopic',
    'Ubuntu Trusty (14.04 LTS)': 'trusty',
}


def get_images(client):
    images = {}
    for i in client.get_images():
        if not i.public:
            continue

        for serie in SERIES_MAP:
            if ("%s" % serie) == i.name:
                images[SERIES_MAP[serie]] = i.id

    return images
