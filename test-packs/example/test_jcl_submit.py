import os
import re

import pytest
from taf import logging
from taf.af_support_tools import get_config_file_option
from taf.zos.jes import JESAdapter

logger = logging.getLogger(__name__)
logger.setLevel('INFO')

config_file = 'config.ini'
username = get_config_file_option(config_file, 'zos_credentials', 'username')
password = get_config_file_option(config_file, 'zos_credentials', 'password')
hostname = get_config_file_option(config_file, 'zos_credentials', 'hostname')


def test_jcl_submit():
    z = JESAdapter(host=hostname, username=username, password=password)
    mydict = {'<UNAME>': username}
    jcl_job = z.submit_jcl(path=os.path.join('resources', 'JCL', 'WHO'),
                           path_relative=True, params=mydict)
    result = jcl_job.spool()
    assert 'J E S 2  J O B  L O G' in result

    match = re.search('.*-\sReturn Code\s+(\d+).*Total\sCPU\sTime.*', result)
    assert match is not None, 'no return code found'
    return_code = match.groups()[0]

    assert return_code == '00', 'non-zero return code'

    logger.info('-------------------------------')
    logger.info(f'return_code: {return_code}')
