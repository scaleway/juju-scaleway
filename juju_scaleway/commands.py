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
import time
import uuid
import yaml

from juju_scaleway import constraints
from juju_scaleway.exceptions import ConfigError, PrecheckError
from juju_scaleway import ops
from juju_scaleway.runner import Runner


logger = logging.getLogger("juju.scaleway")


class BaseCommand(object):

    def __init__(self, config, provider, environment):
        self.config = config
        self.provider = provider
        self.env = environment
        self.runner = Runner()

    def solve_constraints(self):
        start_time = time.time()
        image_map = constraints.get_images(self.provider.client)
        logger.debug("Looked up scaleway images in %0.2f seconds",
                     time.time() - start_time)
        return image_map[self.config.series]

    def check_preconditions(self):
        """Check for provider and configured environments.yaml.
        """
        env_name = self.config.get_env_name()
        with open(self.config.get_env_conf()) as handle:
            conf = yaml.safe_load(handle.read())
            if 'environments' not in conf:
                raise ConfigError(
                    "Invalid environments.yaml, no 'environments' section")
            if env_name not in conf['environments']:
                raise ConfigError(
                    "Environment %r not in environments.yaml" % env_name)
            env = conf['environments'][env_name]
            if not env['type'] in ('null', 'manual'):
                raise ConfigError(
                    "Environment %r provider type is %r must be 'null'" % (
                        env_name, env['type']))
            if env['bootstrap-host']:
                raise ConfigError(
                    "Environment %r already has a bootstrap-host" % (
                        env_name))


class Bootstrap(BaseCommand):
    """
    Actions:
    - Launch an server
    - Wait for it to reach running state
    - Update environment in environments.yaml with bootstrap-host address.
    - Bootstrap juju environment
    Preconditions:
    - named environment found in environments.yaml
    - environment provider type is null
    - bootstrap-host must be null
    - ? existing scaleway with matching env name does not exist.
    """
    def run(self):
        self.check_preconditions()
        image = self.solve_constraints()
        logger.info("Launching bootstrap host (eta 5m)...")
        params = dict(
            name="%s-0" % self.config.get_env_name(), image=image)

        machine = ops.MachineAdd(
            self.provider, self.env, params, series=self.config.series
        )
        server = machine.run()

        logger.info("Bootstrapping environment...")
        try:
            self.env.bootstrap_jenv(server.public_ip['address'])
        except:
            self.provider.terminate_server(server.id)
            raise
        logger.info("Bootstrap complete.")

    def check_preconditions(self):
        result = super(Bootstrap, self).check_preconditions()
        if self.env.is_running():
            raise PrecheckError(
                "Environment %s is already bootstrapped" % (
                    self.config.get_env_name()))
        return result


class ListMachines(BaseCommand):

    def run(self):
        env_name = self.config.get_env_name()
        header = "{:<8} {:<18} {:<8} {:<12} {:<10}".format(
            "Id", "Name", "Status", "Created", "Address")

        allmachines = self.config.options.all
        for server in self.provider.get_servers():
            name = server.name

            if not allmachines and not name.startswith('%s-' % env_name):
                continue

            if header:
                print(header)
                header = None

            if len(name) > 18:
                name = name[:15] + "..."

            print("{:<8} {:<18} {:<8} {:<12} {:<10}".format(
                server.id,
                name,
                server.state,
                server.creation_date[:-10],
                server.public_ip['address'] if server.public_ip else 'none'
            ).strip())


class AddMachine(BaseCommand):

    def run(self):
        self.check_preconditions()
        image = self.solve_constraints()
        logger.info("Launching %d servers...", self.config.num_machines)

        template = dict(
            image=image)

        for _ in range(self.config.num_machines):
            params = dict(template)
            params['name'] = "%s-%s" % (
                self.config.get_env_name(), uuid.uuid4().hex)
            self.runner.queue_op(
                ops.MachineRegister(
                    self.provider, self.env, params, series=self.config.series
                )
            )

        for (server, _) in self.runner.iter_results():
            logger.info(
                "Registered id:%s name:%s ip:%s as juju machine",
                server.id, server.name,
                server.public_ip['address'] if server.public_ip else None
            )


class TerminateMachine(BaseCommand):

    def run(self):
        """Terminate machine in environment.
        """
        self.check_preconditions()
        self._terminate_machines(lambda x: x in self.config.options.machines)

    def _terminate_machines(self, machine_filter):
        logger.debug("Checking for machines to terminate")
        status = self.env.status()
        machines = status.get('machines', {})

        # Using the api server-id can be the provider id, but
        # else it defaults to ip, and we have to disambiguate.
        remove = []
        for machine in machines:
            if machine_filter(machine):
                remove.append({
                    'address': machines[machine]['dns-name'],
                    'server_id': machines[machine]['instance-id'],
                    'machine_id': machine
                })

        address_map = dict([
            (d.public_ip['address'] if d.public_ip else None, d)
            for d in self.provider.get_servers()
        ])
        if not remove:
            return status, address_map

        logger.info(
            "Terminating machines %s",
            " ".join([machine['machine_id'] for machine in remove])
        )

        for machine in remove:
            server = address_map.get(machine['address'])
            env_only = False  # Remove from only env or also provider.
            if server is None:
                logger.warning(
                    "Couldn't resolve machine %s's address %s to server",
                    machine['machine_id'], machine['address']
                )
                # We have a machine in juju state that we couldn't
                # find in provider. Remove it from state so destroy
                # can proceed.
                env_only = True
                server_id = None
            else:
                server_id = server.id
            self.runner.queue_op(
                ops.MachineDestroy(
                    self.provider, self.env, {
                        'machine_id': machine['machine_id'],
                        'server_id': server_id
                    },
                    env_only=env_only
                )
            )
        for _ in self.runner.iter_results():
            pass

        return status, address_map


class DestroyEnvironment(TerminateMachine):

    def run(self):
        """Destroy environment.
        """
        self.check_preconditions()
        force = self.config.options.force

        # Manual provider needs machines removed prior to env destroy.
        def state_service_filter(machine):
            if machine == "0":
                return False
            return True

        if force:
            return self.force_environment_destroy()

        env_status, server_map = self._terminate_machines(
            state_service_filter
        )

        # sadness, machines are marked dead, but juju is async to
        # reality. either sleep (racy) or retry loop, 10s seems to
        # plenty of time.
        time.sleep(10)

        logger.info("Destroying environment")
        self.env.destroy_environment()

        # Remove the state server.
        bootstrap_host = env_status.get(
            'machines', {}).get('0', {}).get('dns-name')
        server = server_map.get(bootstrap_host)
        if server:
            logger.info("Terminating state server")
            self.provider.terminate_server(server.id)
        logger.info("Environment Destroyed")

    def force_environment_destroy(self):
        env_name = self.config.get_env_name()
        env_machines = [m for m in self.provider.get_servers()
                        if m.name.startswith("%s-" % env_name)]

        logger.info("Destroying environment")
        for machine in env_machines:
            self.runner.queue_op(
                ops.MachineDestroy(
                    self.provider, self.env, {'server_id': machine.id},
                    iaas_only=True
                )
            )

        for _ in self.runner.iter_results():
            pass

        # Fast destroy the client cache by removing the jenv file.
        self.env.destroy_environment_jenv()
        logger.info("Environment Destroyed")
