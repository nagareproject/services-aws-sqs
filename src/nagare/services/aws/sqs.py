# --
# Copyright (c) 2014-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

"""Provides classes to interact with the AWS SQS service."""

import re
from concurrent.futures import ThreadPoolExecutor

from nagare.services import proxy, plugin
from nagare.services.aws.resources import AWS


class SQS(plugin.Plugin):
    LOAD_PRIORITY = AWS.LOAD_PRIORITY + 1

    def __init__(self, name, dist, aws_service, services_service, **config):
        services_service(plugin.Plugin.__init__, self, name, dist, **config)
        self.sqs = aws_service.create_resource('sqs')

    @staticmethod
    def to_camelcase(identifier):
        return re.sub('_(.)', lambda m: m.group(1).upper(), '_' + identifier)

    @property
    def queues(self):
        return self.sqs.queues

    def create_queue(self, queue_name, tags=None, **kw):
        attributes = {
            self.to_camelcase(name): str(value).lower() if isinstance(value, bool) else str(value)
            for name, value in kw.items()
            if value is not None
        }

        return self.sqs.create_queue(QueueName=queue_name, Attributes=attributes, tags=tags or {})

    def get_queue(self, queue_name, account_id=None):
        params = {'QueueOwnerAWSAccountId': account_id} if account_id is not None else {}
        return self.sqs.get_queue_by_name(QueueName=queue_name, **params)


class _Queue:
    def __init__(self, queue_name, account_id, pool, creation, tags, sqs_service, **config):
        if creation:
            queue = sqs_service.create_queue(queue_name, tags, **config)
        else:
            queue = sqs_service.get_queue(queue_name, account_id)

        self.queue = queue
        self.pool = pool

    @property
    def dead_letter_source_queues(self):
        return self.dead_letter_source_queues

    def start_consuming(self, callback, **kw):
        with ThreadPoolExecutor(self.pool) as executor:
            while True:
                for msg in self.receive_messages(**kw):
                    executor.submit(callback, msg).add_done_callback(lambda f: f.result())


for method in (
    'add_permission',
    'change_message_visibility_batch',
    'delete',
    'delete_messages',
    'get_available_subresources',
    'load',
    'purge',
    'receive_messages',
    'reload',
    'remove_permission',
    'send_message',
    'send_messages',
    'set_attributes',
):
    setattr(_Queue, method, lambda self, *, _method=method, **kw: getattr(self.queue, _method)(**kw))


@proxy.proxy_to(_Queue, lambda self: self.queues[self.name])
class Queue(plugin.Plugin):
    LOAD_PRIORITY = SQS.LOAD_PRIORITY + 1
    CONFIG_SPEC = plugin.Plugin.CONFIG_SPEC | {
        'queue_name': 'string',
        'account_id': 'string(default=None)',
        'pool': 'integer(default=1)',
        'creation': 'boolean(default=False)',
        'fifo_queue': 'boolean(default=None)',
        'delay_seconds': 'integer(default=0)',
        'maximum_message_size': 'integer(default=262144)',
        'message_retention_period': 'integer(default=345600)',
        'receive_message_wait_time_seconds': 'integer(default=20)',
        'redrive_policy': 'string(default=None)',
        'visibility_timeout': 'integer(default=30)',
        'content_based_deduplication': 'boolean(default=None)',
        'deduplication_scope': 'option(messageGroup, queue, default=None)',
        'fifo_throughput_limit': 'option(perMessageGroupId, perQueue, default=None)',
        'tags': {'___many___': 'string(default=None)'},
    }
    queues = {}

    def __init__(self, name, dist, queue_name, account_id, pool, creation, tags, services_service, **config):
        super().__init__(
            name, dist, queue_name=queue_name, account_id=account_id, pool=pool, creation=creation, tags=tags, **config
        )
        self.__class__.queues[name] = services_service(_Queue, queue_name, account_id, pool, creation, tags, **config)
