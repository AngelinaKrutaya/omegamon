import time
import os
import pytest
from taf.af_support_tools import Config
from taf.zos.jes.adapter import *

logger = logging.getLogger(__name__)
logger.setLevel('INFO')


config_file = Config('config.ini')
username = config_file.get_option('zos_credentials', 'username')
password = config_file.get_option('zos_credentials', 'password')
hostname = config_file.get_option('zos_credentials', 'hostname')


def test_job_wait():
    time1 = int(time.time())
    z = JESAdapter(host=hostname, username=username, password=password, transport='rest')
    jcl = os.path.join(TafVars.af_base_path, 'resources', 'JCL', 'WAIT2MIN')
    job_obj = z.submit_jcl(path=jcl, wait=True)
    result = job_obj.spool(parsed_output=False)
    assert len(result) > 10
    time2 = int(time.time())
    assert (time2-time1) > 100


def test_job_wait_timeout():
    z = JESAdapter(host=hostname, username=username, password=password, transport='rest')
    jcl = os.path.join(TafVars.af_base_path, 'resources', 'JCL', 'WAIT2MIN')
    try:
        z.submit_jcl(path=jcl, wait=True, timeout=60)
    except JobExecutionTimeout:
        assert True
    else:
        assert False, 'JobExecutionTimeout exception was not raised'


def test_job_output_parse():
    z = JESAdapter(host=hostname, username=username, password=password, transport='rest')
    jcl = os.path.join(TafVars.af_base_path, 'resources', 'JCL', 'SYSINFO')
    job_obj = z.submit_jcl(path=jcl, wait=True, save_jcl=False)

    result = job_obj.spool(parsed_output='type1')
    for i in result:
        logger.info('{0} {1}'.format(i, result[i]))

    for i in ['summary', 'statistics', 'steps', 'tail']:
        assert i in result.keys()
