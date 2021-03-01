import os
import string
import random
import pytest

from taf.zos.py3270 import ISPF
from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig

from taf import logging

from libs.creds import *
from libs.ivtenv import rtes


rte = os.environ.get('rte', 'ite4')
hostname = rtes[rte]['hostname']
tems = rtes[rte]['tems']

username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)


logger = logging.getLogger(__name__)

root = TAFConfig().testpack_root


# A fixture returning an ISPF object which is then passed to application fixtures
@pytest.fixture(scope='function')
def ispf(request):
    em = Emulator(hostname, model=2, oversize=(62, 160))
    ispf = ISPF(em, username=username, password=password)
    yield ispf
    ispf.logoff()


# Fixtures returning ISPFPanel objects
@pytest.fixture(scope='function')
def sdsf(ispf):
    sdsf = ispf.start('s.da')
    yield sdsf
    sdsf.exit()


def find_in_sdsf_stc_log(stc, message, sdsf) -> (bool, string):
    """

    :param stc:
    :param message:
    :param sdsf:
    :return: tuple (res, row with message or None)
    """
    not_found = f"LINE NO CHARS  '{message}' FOUND"[0:29].upper()   # 29 is a limit on screen
    found = f"LINE  CHARS '{message}' FOUND"[0:29].upper()  # 29 is a limit on screen
    sdsf(f"pre {stc}")
    sdsf(f"f {stc}")
    sdsf.emulator.display('s', key=keys.ENTER)
    sdsf.emulator.display(f"f '{message}' first", key=keys.ENTER)
    if sdsf.find(not_found):
        return False, None
    elif sdsf.find(found):
        y1, _ = sdsf.emulator.display.get_cursor()
        return True, str(sdsf.emulator.display[y1, :])
    else:
        raise Exception('something went wrong in sdsf find')


# TESTS


@pytest.mark.sp1plus
def test_KRAX279I_message(sdsf):
    """
    https://jira.rocketsoftware.com/browse/ITMZ-844
    """
    message = 'KRAX279I, Private Situation SQL'
    assert find_in_sdsf_stc_log(tems, message, sdsf)[0], f'not found expected {message}'


def test_verify_no_trace_for_hfs(sdsf):
    """
    https://jira.rocketsoftware.com/browse/ITMZ-1263
    Verify that there is no "hfs:" prefixe in the TEMS log.
    We had them even w/ default taces, for example:
     (0004-E4D61493:hfs:kbbssge.c,72,"BSS1_GetEnv") KBS_DEBUG="N"
    """
    message = ':hfs:'    # search is case insensitive, by the way
    assert not find_in_sdsf_stc_log(tems, message, sdsf)[0], f'found unexpected {message}'


def test_verify_sql_trace(sdsf, zosmf):
    """
    https://jira.rocketsoftware.com/browse/ITMZ-1263
    Verify that sql trace works fine: we upload member with SQL to RKANSQL,
    run SPUFIL and check this sql in traces log.
    Log example:
    2020.155 11:40:09.19 (0003-BEC824D3:kdssqprs.c,658,"PRS_ParseSql") SELECT 0CM8U , TRACE9 FROM TRACE.TRACE
    """

    start_trace = f'F {tems},CTDS TRACE ADD FILTER ID=TK1 UNIT=KDSSQPRS CLASS(ALL)'
    stop_trace = f'F {tems},CTDS TRACE REMOVE FILTER ID=TK1'

    member = 'ITMZ1263'
    column = ''.join(random.choices(string.ascii_uppercase + string.digits, k=5))
    sql = f'SELECT {column} , TRACE9 FROM TRACE.TRACE'
    lib = f"{rtes[rte]['rte_hlq']}.RKANSQL({member})"
    cmd = f'F {tems},CTDS START SPUFIL {member}'
    zosmf.write_ds(dataset=lib, data=sql+';')
    try:
        zosmf.issue_command(start_trace)
        zosmf.issue_command(cmd)
        res, row = find_in_sdsf_stc_log(tems, f'"PRS_ParseSql") SELECT {column}', sdsf)
        assert res
        assert sql in row and ':hfs:' not in row
    finally:
        zosmf.issue_command(stop_trace)


def test_verify_prefix_for_trace_ignored(sdsf, zosmf):
    """
    https://jira.rocketsoftware.com/browse/ITMZ-1263
    now prefix is ignored and don't go to the trace itself
    """

    prefix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=4))
    prog = ''.join(random.choices(string.ascii_lowercase + string.digits, k=4))
    expected_trace = f'KBB_RAS1=ERROR (UNIT:{prog} ALL) is now in effect '
    start_trace = f'F {tems},CTDS TRACE ADD FILTER ID=TK1 UNIT={prefix}:{prog} CLASS(ALL)'
    stop_trace = f'F {tems},CTDS TRACE REMOVE FILTER ID=TK1'

    try:
        zosmf.issue_command(start_trace)
        res, row = find_in_sdsf_stc_log(tems, f'(UNIT:{prog} ALL)', sdsf)
        assert res
        assert expected_trace in row
    finally:
        zosmf.issue_command(stop_trace)

