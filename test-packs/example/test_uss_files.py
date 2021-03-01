from os import environ
from sys import platform
from time import time

import pytest
from taf import logging
from taf.af_support_tools import Config
from taf.zos.common.dataset import Dataset
from taf.zos.common.exceptions import DeleteUSSFileError

logger = logging.getLogger(__name__)
logger.setLevel('INFO')

name = 'testfile.txt'
destdir = '/u/ts5721/'
c = Config('config.ini')
hostname = c.get_option('zos_credentials', 'hostname')
username = c.get_option('zos_credentials', 'username')
password = c.get_option('zos_credentials', 'password')


def test_upload_file_uss():
    if platform.startswith('win'):
        fname = f'{environ["TEMP"]}\\{name}'
    else:
        fname = f'/tmp/{name}'
    with open(fname, 'w') as f:
        testdata = str(int(time()))
        f.write(testdata)

    j = Dataset(hostname, username, password)
    j.upload_file_uss(fname, destdir)
    assert j.get_file(f'{destdir}/{name}') == testdata


def test_get_file_contents_from_zos():
    j = Dataset(hostname, username, password)
    result = j.get_file(f'{destdir}/{name}')
    assert type(result) == str
    for i in result:
        logger.info(i)


def test_get_file_list_from_zos():
    j = Dataset(hostname, username, password)
    result = j.list_files(destdir)
    assert type(result) == dict
    logger.info('entry to check: %s' % result[name])
    assert len(result[name]) == 6
    for i in result:
        logger.info('{0} {1}'.format(i, result[i]))


def test_delete_file_uss():
    j = Dataset(hostname, username, password)
    try:
        j.delete_file_uss(f'{destdir}/{name}')
    except DeleteUSSFileError as e:
        raise DeleteUSSFileError(str(e))
