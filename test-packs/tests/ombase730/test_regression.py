import os
import pytest
from taf import logging
from taf.zos.py3270 import keys
import libs.e3270utils as u
from libs.ivtenv import rtes
from libs.creds import *

rte = os.environ.get('rte', 'itcc')
hostname = rtes[rte]['hostname']
applid = rtes[rte]['tom_applid']
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)
rte_hlq = rtes[rte]['rte_hlq']

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def test_enhanced_3270ui_query_error_detected(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.c').enter()
    u.zoom_into_first_row('CICSplex\nName', 'F')
    d.find_by_label('FIND FILE')('MTIDBIN').enter()
    d('7').enter()
    assert not d.find('Query Error Detected')
