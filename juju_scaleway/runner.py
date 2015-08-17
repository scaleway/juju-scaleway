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

"""
Thread based concurrency around bulk ops. scaleway api is sync
"""

import logging

try:
    from Queue import Queue, Empty
except ImportError:  # Python3
    from queue import Queue, Empty

import threading


logger = logging.getLogger("juju.scaleway")


class Runner(object):

    DEFAULT_NUM_RUNNER = 4

    def __init__(self):
        self.jobs = Queue()
        self.results = Queue()
        self.job_count = 0
        self.runners = []
        self.started = False

    def queue_op(self, operation):
        self.jobs.put(operation)
        self.job_count += 1

    def iter_results(self):
        auto = not self.started

        if auto:
            self.start(min(self.DEFAULT_NUM_RUNNER, self.job_count))

        for _ in range(self.job_count):
            self.job_count -= 1
            result = self.gather_result()
            if isinstance(result, Exception):
                continue
            yield result

        if auto:
            self.stop()

    def gather_result(self):
        return self.results.get()

    def start(self, count):
        for _ in range(count):
            runner = OpRunner(self.jobs, self.results)
            runner.daemon = True
            self.runners.append(runner)
            runner.start()
        self.started = True

    def stop(self):
        for runner in self.runners:
            runner.join()
        self.started = False


class OpRunner(threading.Thread):

    def __init__(self, ops, results):
        self.ops = ops
        self.results = results
        super(OpRunner, self).__init__()

    def run(self):
        while 1:
            try:
                operation = self.ops.get(block=False)
            except Empty:
                return

            try:
                result = operation.run()
            except Exception as exc:
                logger.exception("Error while processing op %s", operation)
                result = exc

            self.results.put(result)
