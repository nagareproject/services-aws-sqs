# Encoding: utf-8

# --
# Copyright (c) 2008-2020 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
# --

from os import path

from setuptools import setup, find_packages

here = path.normpath(path.dirname(__file__))

with open(path.join(here, 'README.rst')) as long_description:
    LONG_DESCRIPTION = long_description.read()

setup(
    name='nagare-services-aws-sqs',
    author='Net-ng',
    author_email='alain.poirier@net-ng.com',
    description='Amazon SQS service',
    long_description=LONG_DESCRIPTION,
    license='BSD',
    keywords='',
    url='https://github.com/nagareproject/services-aws-sqs',
    packages=find_packages(),
    zip_safe=False,
    setup_requires=['setuptools_scm'],
    use_scm_version=True,
    install_requires=['nagare-services-aws'],
    entry_points='''
        [nagare.commands]
        aws = nagare.admin.aws.sqs:Commands

        [nagare.commands.aws]
        receive = nagare.admin.aws.sqs:Receive
        send = nagare.admin.aws.sqs:Send

        [nagare.services]
        sqs = nagare.services.aws.sqs:SQS
    '''
)
