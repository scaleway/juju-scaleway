import logging
import time
import uuid
import yaml

from juju_onlinelabs import constraints
from juju_onlinelabs.exceptions import ConfigError, PrecheckError
from juju_onlinelabs import ops
from juju_onlinelabs.runner import Runner


log = logging.getLogger("juju.onlinelabs")


class BaseCommand(object):

    def __init__(self, config, provider, environment):
        self.config = config
        self.provider = provider
        self.env = environment
        self.runner = Runner()

    def solve_constraints(self):
        t = time.time()
        image_map = constraints.get_images(self.provider.client)
        log.debug("Looked up onlinelabs images in %0.2f seconds", time.time() - t)
        return image_map[self.config.series]

    def check_preconditions(self):
        """Check for provider and configured environments.yaml.
        """
        env_name = self.config.get_env_name()
        with open(self.config.get_env_conf()) as fh:
            conf = yaml.safe_load(fh.read())
            if not 'environments' in conf:
                raise ConfigError(
                    "Invalid environments.yaml, no 'environments' section")
            if not env_name in conf['environments']:
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
    - ? existing onlinelabs with matching env name does not exist.
    """
    def run(self):
        self.check_preconditions()
        image = self.solve_constraints()
        log.info("Launching bootstrap host (eta 5m)...")
        params = dict(
            name="%s-0" % self.config.get_env_name(), image=image)

        op = ops.MachineAdd(
            self.provider, self.env, params, series=self.config.series)
        server = op.run()

        log.info("Bootstrapping environment...")
        try:
            self.env.bootstrap_jenv(server.public_ip['address'])
        except:
            self.provider.terminate_server(server.id)
            raise
        log.info("Bootstrap complete.")

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
        for m in self.provider.get_servers():
            if not allmachines and not m.name.startswith('%s-' % env_name):
                continue

            if header:
                print(header)
                header = None

            name = m.name
            if len(name) > 18:
                name = name[:15] + "..."
            print("{:<8} {:<18} {:<8} {:<12} {:<10}".format(
                m.id,
                name,
                m.state,
                m.creation_date[:-10],
                m.public_ip['address'] if m.public_ip else 'none').strip())


class AddMachine(BaseCommand):

    def run(self):
        self.check_preconditions()
        image = self.solve_constraints()
        log.info("Launching %d servers...", self.config.num_machines)

        template = dict(
            image=image)

        for n in range(self.config.num_machines):
            params = dict(template)
            params['name'] = "%s-%s" % (
                self.config.get_env_name(), uuid.uuid4().hex)
            self.runner.queue_op(
                ops.MachineRegister(
                    self.provider, self.env, params, series=self.config.series))


        for (server, machine_id) in self.runner.iter_results():
            log.info("Registered id:%s name:%s ip:%s as juju machine",
                     server.id, server.name, server.public_ip['address'] if server.public_ip else None)


class TerminateMachine(BaseCommand):

    def run(self):
        """Terminate machine in environment.
        """
        self.check_preconditions()
        self._terminate_machines(lambda x: x in self.config.options.machines)

    def _terminate_machines(self, machine_filter):
        log.debug("Checking for machines to terminate")
        status = self.env.status()
        machines = status.get('machines', {})

        # Using the api server-id can be the provider id, but
        # else it defaults to ip, and we have to disambiguate.
        remove = []
        for m in machines:
            if machine_filter(m):
                remove.append(
                    {'address': machines[m]['dns-name'],
                     'server_id': machines[m]['instance-id'],
                     'machine_id': m})

        address_map = dict([(d.public_ip['address'] if d.public_ip else None, d) for
                            d in self.provider.get_servers()])
        if not remove:
            return status, address_map

        log.info("Terminating machines %s",
                 " ".join([m['machine_id'] for m in remove]))

        for m in remove:
            server = address_map.get(m['address'])
            env_only = False  # Remove from only env or also provider.
            if server is None:
                log.warning(
                    "Couldn't resolve machine %s's address %s to server" % (
                        m['machine_id'], m['address']))
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
                        'machine_id': m['machine_id'],
                        'server_id': server_id},
                    env_only=env_only))
        for result in self.runner.iter_results():
            pass

        return status, address_map


class DestroyEnvironment(TerminateMachine):

    def run(self):
        """Destroy environment.
        """
        self.check_preconditions()
        force = self.config.options.force

        # Manual provider needs machines removed prior to env destroy.
        def state_service_filter(m):
            if m == "0":
                return False
            return True

        if force:
            return self.force_environment_destroy()

        env_status, server_map = self._terminate_machines(
            state_service_filter)

        # sadness, machines are marked dead, but juju is async to
        # reality. either sleep (racy) or retry loop, 10s seems to
        # plenty of time.
        time.sleep(10)

        log.info("Destroying environment")
        self.env.destroy_environment()

        # Remove the state server.
        bootstrap_host = env_status.get(
            'machines', {}).get('0', {}).get('dns-name')
        server = server_map.get(bootstrap_host)
        if server:
            log.info("Terminating state server")
            self.provider.terminate_server(server.id)
        log.info("Environment Destroyed")

    def force_environment_destroy(self):
        env_name = self.config.get_env_name()
        env_machines = [m for m in self.provider.get_servers()
                        if m.name.startswith("%s-" % env_name)]

        log.info("Destroying environment")
        for m in env_machines:
            self.runner.queue_op(
                ops.MachineDestroy(
                    self.provider, self.env, {'server_id': m.id},
                    iaas_only=True))

        for result in self.runner.iter_results():
            pass

        # Fast destroy the client cache by removing the jenv file.
        self.env.destroy_environment_jenv()
        log.info("Environment Destroyed")
