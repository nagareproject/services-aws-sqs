# --
# Copyright (c) 2014-2025 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

import time

from nagare.admin import command


class Commands(command.Commands):
    DESC = 'AWS SQS subcommands'


class Receive(command.Command):
    WITH_STARTED_SERVICES = True
    DESC = 'receive data from a queue'

    def __init__(self, name, dist, **config):
        super().__init__(name, dist, **config)
        self.nb = 0

    def set_arguments(self, parser):
        parser.add_argument('queue', help='queue service')

        super().set_arguments(parser)

    def handle_request(self, msg):
        print(f'- {self.nb} --------------------')

        print(f'Id: {msg.message_id}')

        if msg.attributes:
            print('Attributes:')

            padding = len(max(msg.attributes, key=len))
            for k, v in sorted(msg.attributes.items()):
                print(' - {}: {}'.format(k.ljust(padding), v))

        if msg.message_attributes:
            print('Message attributes:')

            padding = len(max(msg.message_attributes, key=len))
            for k, v in sorted(msg.message_attributes.items()):
                print(' - {}: {}'.format(k.ljust(padding), v))

        print(f'Body: {msg.body}')

        self.nb += 1
        print('')

        msg.delete()

    def run(self, queue, services_service):
        queue = services_service[queue]
        print(f'Listening on <{queue.name}>...')

        queue.start_consuming(self.handle_request, AttributeNames=['All'], MessageAttributeNames=['All'])

        return 0


class Send(command.Command):
    WITH_STARTED_SERVICES = True
    DESC = 'send data to a queue'

    def set_arguments(self, parser):
        parser.add_argument('-g', '--group', help='MessageGroupId')
        parser.add_argument(
            '-a', '--attr', action='append', metavar=('name', 'value'), nargs=2, help='message attributes'
        )
        parser.add_argument('-l', '--loop', action='store_true', help='infinite loop sending <data> each 2 seconds')

        parser.add_argument('queue', help='queue service')
        parser.add_argument('data', help='data to send')

        super().set_arguments(parser)

    @staticmethod
    def run(loop, queue, group, data, attr, services_service):
        queue = services_service[queue]
        attrs = {name: {'StringValue': value, 'DataType': 'String'} for name, value in (attr or ())}

        try:
            while True:
                params = {'MessageGroupId': group} if group else {}
                queue.send_message(MessageBody=data, MessageAttributes=attrs, **params)
                time.sleep(1)

                if not loop:
                    break
        except KeyboardInterrupt:
            pass

        return 0
