Juju Scaleway provider
======================

Stable release: |release| |license| |dependencies| |popularity|

Development: |build| |quality| |coverage|

.. |release| image:: https://img.shields.io/pypi/v/juju-scaleway.svg?style=flat
    :target: https://pypi.python.org/pypi/juju-scaleway
    :alt: Last release
.. |license| image:: https://img.shields.io/pypi/l/juju-scaleway.svg?style=flat
    :target: http://opensource.org/licenses/BSD-2-Clause
    :alt: Software license
.. |popularity| image:: https://img.shields.io/pypi/dm/juju-scaleway.svg?style=flat
    :target: https://pypi.python.org/pypi/juju-scaleway#downloads
    :alt: Popularity
.. |dependencies| image:: https://img.shields.io/requires/github/scaleway/juju-scaleway/master.svg?style=flat
    :target: https://requires.io/github/scaleway/juju-scaleway/requirements/?branch=master
    :alt: Requirements freshness
.. |build| image:: https://img.shields.io/travis/scaleway/juju-scaleway/develop.svg?style=flat
    :target: https://travis-ci.org/scaleway/juju-scaleway
    :alt: Unit-tests status
.. |coverage| image::  https://coveralls.io/repos/scaleway/juju-scaleway/badge.svg?branch=develop&service=github
    :target: https://coveralls.io/r/scaleway/juju-scaleway?branch=develop
    :alt: Coverage Status
.. |quality| image:: https://img.shields.io/scrutinizer/g/scaleway/juju-scaleway.svg?style=flat
    :target: https://scrutinizer-ci.com/g/scaleway/juju-scaleway/?branch=develop
    :alt: Code Quality

This package provides a CLI plugin for `Juju <http://juju.ubuntu.com>`_ to
provision physical servers on `Scaleway <https://scaleway.com>`_, the first
platform to offer dedicated ARM servers in the cloud.

Juju provides for workloads management and orchestration using a collection of
workloads definitions (charms) that can be assembled lego fashion at runtime
into complex application topologies.

This plugin is highly inspired by `@kapilt <https://github.com/kapilt>`_ Juju
plugins.


Installation
============

Linux
-----

A usable version of Juju is available out of the box in Ubuntu 14.04 and later
versions. For earlier versions of Ubuntu, please use the stable PPA:

.. code-block:: bash

    $ sudo add-apt-repository ppa:juju/stable
    $ apt-get update && apt-get install juju


Mac OS X
--------

Juju is in Homebrew. To install Juju it is required to have `homebrew
<http://brew.sh>`_ installed. To install Juju run the following command:

.. code-block:: bash

    $ brew install juju


Plugin install (any OS)
-----------------------

Plugin installation is done via ``pip`` which is the python language package
managers, its available by default on Ubuntu. Also recommended is
``virtualenv`` to sandbox this install from your system packages:

.. code-block:: bash

    $ pip install -U juju-scaleway


Setup
=====

**Requirements**:

- You have an account and are logged into `scaleway.com
  <https://scaleway.com>`_;
- You have configured your `SSH Key
  <https://scaleway.com/docs/configure_new_ssh_key>`_.


Scaleway API keys
-----------------

Provide the credentials required by the plugin using environment variables:

.. code-block:: bash

    $ export SCALEWAY_ACCESS_KEY=<organization_key>
    $ export SCALEWAY_SECRET_KEY=<secret_token>


Juju configuration
------------------

To configure a Juju environment for Scaleway, add the following in your
``~/.juju/environments.yaml``:

.. code-block:: yaml

    environments:
        scaleway:
            type: manual
            bootstrap-host: null
            bootstrap-user: root


Usage
=====

You have to tell Juju which environment to use. One way to do this is to use
the following command:

.. code-block:: bash

    $ juju switch scaleway
    $ export JUJU_ENV=scaleway

Now you can bootstrap your Scaleway environment:

.. code-block:: bash

    $ juju scaleway bootstrap

All machines created by this plugin will have the Juju environment name as a
prefix for their servers name.

After your environment is bootstrapped you can add additional machines to it
via the the add-machine command, for instance the following will add 2
additional machines:

.. code-block:: bash

    $ juju scaleway add-machine -n 2
    $ juju status

You can now use standard Juju commands for deploying service workloads aka
charms:

.. code-block:: bash

    $ juju deploy wordpress

Without specifying the machine to place the workload on, the machine will
automatically go to an unused machine within the environment.

There are hundreds of available charms ready to be used, you can find out more
about what's out there from at `jujucharms.com <http://jujucharms.com>`_. Or
alternatively the `'plain' html version
<http://manage.jujucharms.com/charms/precise>`_.

You can use manual placement to deploy target particular machines:

.. code-block:: bash

    $ juju deploy mysql --to=2

And of course the real magic of Juju comes in its ability to assemble these
workloads together via relations like lego blocks:

.. code-block:: bash

    $ juju add-relation wordpress mysql

You can list all machines in Scaleway that are part of the Juju environment
with the list-machines command. This directly queries the Scaleway API and does
not interact with Juju API.

.. code-block:: bash

    $ juju scaleway list-machines

    Id       Name               Status   Created      Address
    6222349  scaleway-0            active   2014-11-25   212.47.239.232
    6342360  scaleway-ef19ad5cc... active   2014-11-25   212.47.228.28
    2224321  scaleway-145bf7a80... active   2014-11-25   212.47.228.79

You can terminate allocated machines by their machine ID. By default with the
Scaleway plugin, machines are forcibly terminated which will also terminate any
service units on those machines:

.. code-block:: bash

    $ juju scaleway terminate-machine 1 2

And you can destroy the entire environment via:

.. code-block:: bash

    $ juju scaleway destroy-environment

``destroy-environment`` also takes a ``--force`` option which only uses the
Scaleway API. Its helpful if state server or other machines are killed
independently of Juju.

All commands have builtin help facilities and accept a ``-v`` option which will
print verbose output while running.

You can find out more about using from `Juju docs
<http://juju.ubuntu.com/docs>`_.


License
=======

This software is licensed under a `BSD 2-Clause License
<https://github.com/scaleway/juju-scaleway/blob/develop/LICENSE.rst>`_.
