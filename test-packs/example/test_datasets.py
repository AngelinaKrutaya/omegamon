import os

import pytest
from taf import logging
from taf.af_support_tools import TafVars, Config
from taf.zos.common.dataset import Dataset

logger = logging.getLogger(__name__)

dest = 'MYDATASET.MYMEMBER'  # dataset to work with
ds_mask = f'{dest.split(".")[0]}.*'  # dataset mask to get list of
c = Config('config.ini')
hostname = c.get_option('zos_credentials', 'hostname')
username = c.get_option('zos_credentials', 'username')
password = c.get_option('zos_credentials', 'password')


def test_01_upload_ds(json_metadata):
    json_metadata['details'] = {
        "TCDescription": "Delete if exist, Upload"}
    source = os.path.join(TafVars.af_base_path, 'resources', 'JCL')

    z = Dataset(hostname, username, password)
    if dest in z.list_ds(dest):
        result = z.del_ds(dest)
        assert result[0], result[1]

    result = z.upload_ds(source, dest)
    assert result[0], result[1]


def test_02_list_ds():
    z = Dataset(hostname, username, password)
    logger.info(f'dataset to list: {ds_mask}')
    result = z.list_ds(ds_mask)
    logger.info(result)
    assert type(result) == tuple
    assert len(result) > 0

    result = z.list_pds(dest)
    logger.info(f'partitioned dataset to get list of members from: {dest}')
    logger.info(f'members:, {result}')
    assert type(result) == tuple
    assert len(result) > 0


def test_03_get_ds():
    z = Dataset(hostname, username, password)
    member1 = 'SYSINFO'
    member2 = 'WHO'
    result = z.get_ds(dest + '(' + member1 + ', ' + member2 + ')')
    assert type(result) == dict
    assert len(result.keys()) > 0
    logger.info('member1 name: %s' % member1)
    logger.info('number of lines in the member1: %s' % len(result[member1]))
    logger.info('member2 name: %s' % member2)
    logger.info('number of lines in the member2: %s' % len(result[member2]))
    assert len(result[member1]) > 0
    assert len(result[member2]) > 0


def test_04_delete_ds():
    z = Dataset(hostname, username, password)
    test_01_upload_ds({})
    result = z.del_ds(dest)
    assert result[0]
