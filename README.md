# Juju Scaleway provider

This package provides a cli plugin for Juju that allows for automated
provisioning of physical servers on Scaleway.

Scaleway is the first hosting provider worldwide to offer dedicated arm servers in the cloud.

Juju provides for workloads management and orchestration using a
collection of workloads definitions (charms) that can be assembled
lego fashion at runtime into complex application topologies.

You can find out more about Juju at its home page. http://juju.ubuntu.com

This plugin is highly inspired from [kapilt](https://github.com/kapilt) Juju plugins.

## Installation

### Linux

A usable version of Juju is available out of the box in Ubuntu 14.04 and later
versions. For earlier versions of Ubuntu, please use the stable ppa:

```
$ sudo add-apt-repository ppa:juju/stable
$ apt-get update && apt-get install juju
```

### Mac OS X

Juju is in Homebrew. To install Juju it is required to have homebrew installed [brew.sh](http://brew.sh/).
To install Juju run the following command:

```
$ brew install juju
```

### Plugin install (Any OS)

Plugin installation is done via pip/easy_install which is the python language
package managers, its available by default on Ubuntu. Also recommended
is virtualenv to sandbox this install from your system packages::

```
$ pip install -U juju-scaleway
```

## Setup

> <strong>Requirements</strong>
>
- You have an account and are logged into [cloud.scaleway.com](https://cloud.scaleway.com)
- You have configured your [SSH Key](https://www.scaleway.com/docs/configure_new_ssh_key)

### Scaleway API keys

Provide the credentials required by the plugin using environment variables:

```
$ export SCALEWAY_ACCESS_KEY=<organization_key>
$ export SCALEWAY_SECRET_KEY=<secret_token>
```

### Juju configuration

To configure a Juju environment for Scaleway, add the following in your '~/.juju/environments.yaml':

```
environments:
    scaleway:
       type: manual
       bootstrap-host: null
       bootstrap-user: root
```

## Usage

You have to tell Juju which environment to use.
One way to do this is to use the following command:

```
$ juju switch scaleway
$ export JUJU_ENV=scaleway
```

Now you can bootstrap your Scaleway environment:

```
$ juju scaleway bootstrap
```

All machines created by this plugin will have the Juju environment
name as a prefix for their servers name.

After your environment is bootstrapped you can add additional machines
to it via the the add-machine command, for instance the following will
add 2 additional machines:

```
$ juju scaleway add-machine -n 2
$ juju status
```

You can now use standard Juju commands for deploying service workloads aka
charms:

```
$ juju deploy wordpress
```

Without specifying the machine to place the workload on, the machine
will automatically go to an unused machine within the environment.

There are hundreds of available charms ready to be used, you can
find out more about what's out there from http://jujucharms.com
Or alternatively the 'plain' html version at
http://manage.jujucharms.com/charms/precise

You can use manual placement to deploy target particular machines:

```
$ juju deploy mysql --to=2
```

And of course the real magic of Juju comes in its ability to assemble
these workloads together via relations like lego blocks:

```
$ juju add-relation wordpress mysql
```

You can list all machines in Scaleway that are part of the Juju
environment with the list-machines command. This directly queries the
Scaleway api and does not interact with Juju api.

```
$ juju scaleway list-machines

Id       Name               Status   Created      Address
6222349  scaleway-0            active   2014-11-25   212.47.239.232
6342360  scaleway-ef19ad5cc... active   2014-11-25   212.47.228.28
2224321  scaleway-145bf7a80... active   2014-11-25   212.47.228.79
```

You can terminate allocated machines by their machine id. By default with the
Scaleway plugin, machines are forcibly terminated which will also terminate any
service units on those machines:

```
$ juju scaleway terminate-machine 1 2
```

And you can destroy the entire environment via:

```
$ juju scaleway destroy-environment
```

destroy-environment also takes a --force option which only uses the
Scaleway api. Its helpful if state server or other machines are
killed independently of Juju.

All commands have builtin help facilities and accept a -v option which will
print verbose output while running.

You can find out more about using from http://juju.ubuntu.com/docs
