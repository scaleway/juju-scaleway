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


class ConfigError(ValueError):
    """ Environments.yaml configuration error.
    """


class PrecheckError(ValueError):
    """ A precondition check failed.
    """


class ConstraintError(ValueError):
    """ Specificed constraint is invalid.
    """


class TimeoutError(ValueError):
    """ Instance could not be provisioned before timeout.
    """


class ProviderError(Exception):
    """Instance could not be provisioned.
    """


class ProviderAPIError(Exception):

    def __init__(self, response, message):
        self.response = response
        self.message = message

    def __str__(self):
        return "<ProviderAPIError message:%s response:%r>" % (
            self.message or "Unknown",
            self.response.status_code)
