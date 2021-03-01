import pytest

from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig

from taf import logging

from libs.ite1zos import *


logger = logging.getLogger(__name__)


root = TAFConfig().testpack_root

display = None


@pytest.fixture(scope='module')
def classic_in_out(request):
    global display
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(43, 80))
    try:
        d = em.display
        display = em.display

        welcome = d.find('===> Ex.: LOGON <userid>, TSO <userid>')
        if welcome:
            logger.info(f"Logging to Classic applid {applid}")
            welcome.shift((1, 0))(f"L {applid} DATA='LROWS=9999'", keys.ENTER, 240)

        if d.find('ENTER USERID'):
            d(user, keys.NEWLINE)
            d(password, keys.ENTER)
        else:
            d(key=keys.ENTER, timeout=30)

        assert d.find('ZMENU    VTM     OM/DEX')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
    finally:
        em.disconnect()
        em.close()


def setup_module(module):
    pass
    # utils.set_security(hostname, username, password, rte_hlq, rte_name, omegamon, 'passphrase', ('KOMSUPD', 'KOMRACFA'), stc_job)


#### TESTS


def test_working_set(classic_in_out):
    d = classic_in_out
    d('J.F', key=keys.ENTER )
    assert d.find('ZSTC     VTM')
    d.find('XCFAS')(key=keys.PF11)
    assert d.find('ZIN      VTM')
    d('C', key=keys.ENTER )
    assert d.find('ZZJOBDB  VTM')
    assert d.find(regex='Working Set ?[0-9]{3,5}K.*')


def test_working_set_and_aenv(classic_in_out):
    """
    Test compares 'Working Set' value from 2 sources, when FreeMained Frames support
    was not considrered (and it is switched on), values were differ
    """
    d = classic_in_out
    d('E', key=keys.ENTER )
    command = d.find('>                            EXCEPTION INFORMATION')
    command('JOBN     XCFAS', key=keys.ENTER)
    command.shift((1, 0))('.aenv', keys.ENTER, 240)
    d(key=keys.ENTER )
    command = d.find('_ A  OPS ..........')
    command(key=keys.ERASEEOF)
    command('wkst', key=keys.ENTER)
    short_column = d.find('- Short').bottom
    wkst_line = d.find('+      Working Set').right
    aenv_wkst_value = str(short_column & wkst_line).strip()
    wkst_wkst_value = str(command).split()[1].strip()
    assert aenv_wkst_value == wkst_wkst_value


def test_swapped_out_message(classic_in_out):
    """
    Test to check message for swapped out applications.
    """
    d = classic_in_out
    d('J.F', key=keys.ENTER )
    if d.find('TSO'):
        d.find('TSO')('',keys.PF11, 30)
    else:
        d.find('INETD1')('',keys.PF11, 30)
    d('C', keys.ENTER, 30)
    assert d.find('>> Address space is swapped out <<')


def test_working_set_and_aenv_all_stcs(classic_in_out):
    """
    Test compares 'Working Set' value from 2 sources, when FreeMained Frames support
    was not considrered (and it is switched on), values were differ
    """
    count = 0
    stc_set = set()
    d = classic_in_out
    d('J.F', key=keys.ENTER )
    all_areas = d.find_all(regex='STCJ  .*')
    # for ar in all_areas[-2:]:
    for ar in all_areas:
        for stc_name in map(str.strip, str(ar).split()):
            # some special cases and when stc has gone already
            if stc_name == 'STCJ' or stc_name.strip() == '+' or not d.find(stc_name):
                continue
            # skip dup stc names
            if stc_name in stc_set:
                continue
            else:
                stc_set.add(stc_name)
            # if stc_name == '.RC':
            #     pass
            # print(str(ar))
            # print(map(str.strip, str(ar).split()))
            count += 1
            d.find(stc_name).shift((0, 1))('', keys.PF11, 30)
            d('C', keys.ENTER, 30)
            if not d.find('is swapped out'):
                command = d.find('+      Pg-in/CPU-s')
                assert command, f'{stc_name} {str(ar)}'
                command = command.shift((1, 0))
                command('wkst', keys.ENTER, 30)
                short_column = d.find('- Short').bottom
                wkst_line = d.find('+      Working Set').right
                aenv_wkst_value = str(short_column & wkst_line).strip()

                if not aenv_wkst_value.endswith('M'):
                    #in this case, values will be different
                    wkst_wkst_value = str(command).split()[1].strip()
                    assert aenv_wkst_value == wkst_wkst_value, stc_name
            d(key=keys.PF3)
            d(key=keys.PF3)
    assert count > 0, count


def test_sys_env(classic_in_out):
    d = classic_in_out
    d('E', key=keys.ENTER)
    command = d.find('>                            EXCEPTION INFORMATION')
    command('.sys', key=keys.ENTER)
    assert d.find('.SYS    >> WLM Goal mode OPT=')
    command.shift((1, 0))('.env', keys.ENTER, 240)
    assert d.find(regex='z/OS   02.0[234].00 running')
    assert d.find(regex='IPLed at  ?[0-9:]{7,8}  on [0-9/]{8}   RMF [0-9]{3}    is active')


# def test_build_level(classic_in_out):
#     d = classic_in_out
#     d('E', key=keys.ENTER )
#     command = d.find('>                            EXCEPTION INFORMATION')
#     command('.mod', key=keys.ENTER)
#     assert d.find('7/1/2019')


def test_exceptions_ZEXCP_ZOPS(classic_in_out):
    d = classic_in_out
    d('E.A', key=keys.ENTER )
    assert d.find('ZOPS')
    assert d.find('OPERATION STATUS')
    assert d.find('CPU Utilization')
    assert d.find(regex='FXFR STC *MASTER*    | Fixed Frames in use = [0-9]{3,5}')


def test_exceptions_ZEXCP_ZALL(classic_in_out):
    d = classic_in_out
    d('E.B', key=keys.ENTER )
    assert d.find('ZALL')
    assert d.find('SYSTEM WIDE EXCEPTIONS')
    assert d.find('OMEGAMON/MVS Exception Analysis')
    assert d.find(regex='FXFR STC *MASTER*    | Fixed Frames in use = [0-9]{3,5}')


def test_exceptions_ZEXCP_ZXTRP(classic_in_out):
    d = classic_in_out
    # need to go to system exceptions first to get history, this is a workaround
    d('E.B', key=keys.ENTER )
    d(key=keys.PF3 )
    d('C', key=keys.ENTER )
    assert d.find('ZXTRP')
    assert d.find('EXCEPTION HISTORY')
    assert d.find('+ WAIT')
    assert d.find('+ WSHI')


def test_job_analysis_tso_users(classic_in_out):
    d = classic_in_out
    d('J.A', key=keys.ENTER )
    assert d.find('ZTSO')
    assert d.find('TSO USERS')
    assert d.find('Number of Users Logged On')
    assert d.find('TSO Users Currently in a Transaction')
    assert d.find('For more information on a TSO user')


def test_job_analysis_batch(classic_in_out):
    d = classic_in_out
    d('J.B', key=keys.ENTER )
    assert d.find('ZBATCH')
    assert d.find('BATCH JOBS')
    assert d.find('BATX\nstep\n\ntmtr\nwait\njsta\nswpr\n\ntcp2.S\nioj .S\nrcp%\ncpu2')


def test_job_analysis_wait(classic_in_out):
    d = classic_in_out
    d('J.C', key=keys.ENTER )
    assert d.find('ZBWAT')
    assert d.find('BATCH JOBS WAITING')
    assert d.find('BWAT\nstep\n\nelap\nwait\nwatl\njsta\nswpr')


def test_job_analysis_swapped(classic_in_out):
    d = classic_in_out
    d('J.D', key=keys.ENTER )
    assert d.find('ZBSWP')
    assert d.find('SWAPPED OUT BATCH JOBS')
    assert d.find('BSWP\nstep\n\nelap\njsta\nswpr')


def test_job_analysis_stc(classic_in_out):
    d = classic_in_out
    d('J.F', key=keys.ENTER )
    assert d.find('ZSTC')
    assert d.find('STARTED TASKS')
    assert d.find('STCJ\nioj .S \ncpu2.S')

