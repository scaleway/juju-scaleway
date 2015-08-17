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

import subprocess

# juju-core will defer to either ssh or go.crypto/ssh impl
# these options are only for the ssh ops below (availability
# check and apt-get update on precise instances).
SSH_CMD = ("/usr/bin/ssh",
           "-o", "StrictHostKeyChecking=no",
           "-o", "UserKnownHostsFile=/dev/null")


def check_ssh(host, user="root"):
    cmd = list(SSH_CMD) + ["%s@%s" % (user, host), "ls"]
    process = subprocess.Popen(
        args=cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    output, err = process.communicate()
    retcode = process.poll()

    if retcode:
        raise subprocess.CalledProcessError(
            retcode, cmd, '%s%s' % (output, err or '')
        )
    return True


def update_instance(host, user="root"):
    base = list(SSH_CMD) + ["%s@%s" % (user, host)]
    subprocess.check_output(
        base + ["apt-get", "update"], stderr=subprocess.STDOUT
    )
