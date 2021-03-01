import pytest
import os
import logging

from taf.zos.py3270 import keys

import libs.e3270utils as e3270u
from libs.creds import *
from libs.ivtenv import rtes
import libs.utils as util
from taf.zos.zosmflib import zOSMFConnector
from taf.zos.zftplib import ZFTP
import re
import time

rte = os.environ.get('rte', 'ite1')
hostname = rtes[rte]['hostname']
applid = rtes[rte]['tom_applid']
hubname = rtes[rte]['hub_name']
hlq = rtes[rte]['rte_hlq']
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

z = zOSMFConnector(hostname, username, password)


def choose_multi(parameter):
    data = z.read_ds(f'ROCKET.USER.PROCLIB({rtes[rte]["tom_stc"]})')
    data = re.sub(r'/\/\[*]?(\s+)\'MULTI=[N,Y]\',', f"//          'MULTI={parameter}',", data)
    z.write_ds(f'ROCKET.USER.PROCLIB({rtes[rte]["tom_stc"]})', data)
    util.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, 'dataset', 'multi', (),
                      rtes[rte]['tom_stc'], 120)


def setup_module(module):
    choose_multi('Y')


def teardown_module(module):
    choose_multi('N')


@pytest.fixture(scope='module')
def e3270_special():
    em = e3270u.logon_beacon(hostname, applid, username=username[:-1], password=password)
    try:
        display = em.display
        yield display
    finally:
        e3270u.close_beacon(em)


# TESTS-------------------------------------------------------------------------------

# This test need to run before all the regression tests. It checks the correctly HUB_name.
# And the userid profile has in the UKOBDATF.
# NB: we don't need this as we copy profiles explicitly


def check_hub_and_profile(letter):
    try:
        text = z.read_ds(dataset=f'{hlq}.UKOBDATF({username[:-1] + letter})')
        match = re.search(hubname, text)
        if match is None:
            logger.info(f"Change HUB in {username[:-1] + letter} profile in UKOBDATF!")
            return False
    except:
        logger.info(f"No {username[:-1] + letter} profile in"
                    f" {hlq}.UKOBDATF)."
                    f"Logon with {username[:-1] + letter} ")
        return False


# ---------------------------------------------------------------------------------------

# @pytest.mark.skipif(check_hub_and_profile('A') is False or check_hub_and_profile('B') is False,
#                     reason=f"RTE doesn't have {username}/B profiles in UKOBDATF")
def test_no_super_user_cannot_get_access_to_any_member_of_rte(e3270_in_out):
    d = e3270_in_out
    d.find('«')('').enter()
    assert not d.find('RTE')


def test_several_file_menu_options_are_disabled_for_unpriviledged_user(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    for option in ['o', 's']:
        current_panel = e3270u.get_current_panel(d)
        d('f.' + option).enter()
        assert current_panel == e3270u.get_current_panel(d)


def test_several_edit_menu_options_are_disabled_for_unpriviledged_user(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    for option in ['s', 'o']:
        current_panel = e3270u.get_current_panel(d)
        d('e.' + option).enter()
        assert current_panel == e3270u.get_current_panel(d)


def test_several_view_menu_options_are_disabled_for_unpriviledged_user(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    for option in ['f', 's', 'w', 'r']:
        current_panel = e3270u.get_current_panel(d)
        d('v.' + option).enter()
        assert current_panel == e3270u.get_current_panel(d)


def test_several_tools_menu_options_are_disabled_for_unpriviledged_user(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    for option in ['a', 'u', 'h', 'p', 's', 'd', 'v', 'o']:
        current_panel = e3270u.get_current_panel(d)
        d('t.' + option).enter()
        assert current_panel == e3270u.get_current_panel(d)


def test_panel_session_logon_is_disabled(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('e.p', key=keys.ENTER, timeout=30)
    assert e3270u.get_current_panel(d) == 'KOBPRFCL'
    e3270u.click_tab(' Session/Logon ', d=d)
    # we must stay on the same panel
    assert e3270u.get_current_panel(d) == 'KOBPRFCL'
    assert not e3270u.get_current_panel(d) == 'KOBPRFSS'


def config():
    try:
        text_in_member = z.read_ds(dataset=f'{hlq}.UKOBDATF(KOBUSER)')
        group_user = re.search(f'USERID:{username.upper()}\s+GROUP:(\w+)', text_in_member).group(1)
        text = z.read_ds(dataset=f'{hlq}.UKOBDATF(KOBGROUP)')
        match = re.search(group_user, text)
        if match:
            text_in_member = z.read_ds(dataset=f'{hlq}.UKOBDATF(KOBGROUP)')
            product, match = re.search('GROUP:' + group_user + ',FIRSTWS=\w+,(\n\S+)(\n\S+)', text_in_member).group(1,
                                                                                                                    2)
            nav = [m.group(2) for m in re.finditer("(SHOW\w+)=(\w)", product + match)]
            return nav
    except:
        print(f'{username} is not in {hlq}.UKOBDATF(KOBUSER)')


@pytest.mark.parametrize("panel",
                         [config()])
def test_verify_tabs_are_shown_according_to_config(panel, e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    counter = 0
    for option in ['e', 'z', 'c', 'g', 'i', 'd', 'm', 'n', 's', 'j']:
        current_panel = e3270u.get_current_panel(d)
        d('n.' + option).enter()
        if panel[counter] == 'Y':
            assert current_panel != e3270u.get_current_panel(d)
        elif panel[counter] == 'N':
            assert current_panel == e3270u.get_current_panel(d)
        counter += 1


# for ITE1: T_D5_Corp1 object group, contains DB2 V11 (IB1A, IBA3)
# for ITE4: T_D5_Corp1 object group, contains DB2 V11 (IB1D, IBD3)
def test_verify_corp1(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.d').enter()
    db2s = e3270u.get_column_list('DB2\nID', 4, d=d)
    if db2s:
        assert all(db2[1] == 'B' for db2 in db2s), 'multi-user sees additional data'
    else:
        assert False, 'multi-user does not have data'


def test_disable_first_workspace(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('e.w').enter()
    assert e3270u.get_current_panel(d) != 'KOBWIZ01'


def test_disable_save_as_pulldown(e3270_in_out):
    d = e3270_in_out
    current_panel = e3270u.get_current_panel(d)
    d(key=keys.HOME)
    d('f.a').enter()
    assert e3270u.get_current_panel(d) == current_panel


def test_dynamic_substitution_ws(e3270_in_out, zosmf):
    '''
    https://jira.rocketsoftware.com/browse/OMBS-1258
    The dynamic substitution of the managed system list was based on application ID.
    It was decided to switch from Product Code matching to NODELIST Name matching.
    '''
    stc_job_id = ''
    for job, data in zosmf.list_jobs(prefix=rtes[rte]['tom_stc'], owner='OMEGSTC').items():
        if data['status'] == 'ACTIVE':
            stc_job_id = job
    text_from_kobuser = zosmf.read_ds(dataset=f'{hlq}.UKOBDATF(KOBUSER)')
    # choose customer for current user
    customer = re.findall(rf'USERID:{username.upper()}\s+GROUP:\w+\s+SUPER:\w+\s+CUSTOMER[:=](\w+)',
                          text_from_kobuser)[0]
    omegs_cust = []
    # select all omegamon msl names for the customer
    text_from_kobcust = zosmf.read_ds(dataset=f'{hlq}.UKOBDATF(KOBCUST)')
    start_text = re.search(rf'CUSTOMER:{customer},\nCUSTNAME:"(.*?)",', text_from_kobcust).end()
    for omegamon, msl_name in re.findall(r'\n(.*?)="(.*?)".*', text_from_kobcust[start_text:]):
        omegs_cust.append((omegamon, msl_name))
    # provided nodelist names for omegamon products
    omegamons = {'z/OS': '*MVS_SYSTEM', 'CICS': '*IBM_CICSplex', 'IMS': '*MVS_IMSPLEX',
                 'DB2': '*MVS_DB2', 'C/TG': '*MVS_CICSTG', 'MQ': '*MVS_MQM',
                 'STOR': '*OMEGAMONXE_SMS', 'MFN': '*OMEGAMONXE_MAINFRAME_NTWK_TCP', 'JVM': '*JVM_Monitor'}
    d = e3270_in_out
    d(key=keys.HOME)
    d('t.i').enter()
    d('b').enter()
    count = 0
    for omegamon, name in omegamons.items():
        d.find(regex=rf'\s+{omegamon}\s+│')('').enter()
        # check msl names in sysprint
        log = zosmf.get_file(jobname=rtes[rte]['tom_stc'], jobid=stc_job_id, section='SYSPRINT')
        assert re.search(
            rf'SYSTEM.PARMA\([\',\"]NODELIST[\',\"],[\',\"]{re.escape(name)}[\',\"],{len(name)}\)[\s,\S]*[+]\n'
            rf'.*SYSTEM.PARMA\([\',\"]NODELIST[\',\"],[\',\"][&]{re.escape(omegs_cust[count][0])}MSL[\',\"],'
            rf'nn\)[\s,\S]*[+]\n'
            rf'.*SYSTEM.PARMA\([\',\"]NODELIST[\',\"],[\',\"]{re.escape(omegs_cust[count][1])}[\',\"],nn\)[\s,\S]*[+]\n'
            rf'.*SYSTEM.PARMA\([\',\"]NODELIST[\',\"],[\',\"]{re.escape(omegs_cust[count][1])}[\',\"],'
            rf'{len(omegs_cust[count][1])}\)', log)
        count += 1


# for ITE1: T_D5_Corp2 object group, contains DB2 V12 (IC1A, ICA4)
# for ITE4: T_D5_Corp1 object group, contains DB2 V12 (IC1D, ICD4)
def test_verify_corp2():
    em = e3270u.logon_beacon(hostname, applid, username=username[:-1] + 'b', password=password)
    try:
        d = em.display
        if d.find('Security system denied request'):
            d(key=keys.PF3)
        d(key=keys.HOME)
        d('n.d').enter()
        db2s = e3270u.get_column_list('DB2\nID', 4, d=d)
        if db2s:
            assert all(db2[1] == 'C' for db2 in db2s), 'multi-user sees additional data'
        else:
            assert False, 'multi-user does not have data'
    finally:
        e3270u.close_beacon(em)


def test_tennant_users_with_no_access_to_zos_are_able_to_view_memory_display():
    data = z.read_ds(f'{hlq}.UKOBDATF(KOBGROUP)')
    start = data.find('TDB2')
    if data.find('SHOWZOS=Y', start):
        data = data.replace('SHOWZOS=Y', 'SHOWZOS=N')
        z.write_ds(f'{hlq}.UKOBDATF(KOBGROUP)', data)
    em = e3270u.logon_beacon(hostname, applid, username, password)
    try:
        d = em.display
        d(key=keys.HOME)
        d('n.z').enter()
        assert e3270u.get_current_panel(d) == 'KOBSEVTS'
        d(key=keys.HOME)
        d('v.m').enter()
        assert e3270u.get_current_panel(d) == 'KOBSEVTS'
    finally:
        e3270u.close_beacon(em)


def test_check_do_not_show_the_first_sub_panel_and_jvm_tree():
    text_from_kobuser = z.read_ds(f'{hlq}.UKOBDATF(KOBUSER)')
    group_user = re.search(f'USERID:{username.upper()}\s+GROUP:(\w+)', text_from_kobuser).group(1)
    text_from_kobgroup = z.read_ds(f'{hlq}.UKOBDATF(KOBGROUP)')
    group_pos = re.search(group_user, text_from_kobgroup).end()
    if text_from_kobgroup.find('SHOWJAVA=Y', group_pos):
        text_changed = text_from_kobgroup.replace('SHOWJAVA=Y', 'SHOWJAVA=N')
        z.write_ds(f'{hlq}.UKOBDATF(KOBGROUP)', text_changed)
    em = e3270u.logon_beacon(hostname, applid, username, password)
    try:
        d = em.display
        d(key=keys.HOME)
        d('=KOBSEVTS').enter()
        assert e3270u.get_current_panel(d) == 'KOBSEVTS'
        assert not d.find(regex=r'Tree\sname\s\S+\s+Options')
        current_panel = e3270u.get_current_panel(d)
        d('n.j').enter()
        assert current_panel == e3270u.get_current_panel(d)
    finally:
        z.write_ds(f'{hlq}.UKOBDATF(KOBGROUP)', text_from_kobgroup)
        e3270u.close_beacon(em)


def test_non_super_user_has_not_access_to_all_db2_ssids_at_both_levels():
    util.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, 'nonsuperuser', 'multi', ())
    em = e3270u.logon_beacon(hostname, applid, username=username[:-1], password=password)
    try:
        d = em.display()
        assert d.find('No Client Defined')
        d(key=keys.HOME)
        d('n.d').enter()
        assert 'Rows:00'
    finally:
        e3270u.close_beacon(em)
        util.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, 'dataset', 'multi', ())


def test_rte_config_accessible_for_privileged_user(e3270_special):
    d = e3270_special
    d.find('«')('').enter()
    d.find('RTE')('').enter()
    e3270u.zoom_in('RKOBPROF', 'B', d=d)
    assert d.find('RKOBPROF Member List')


def test_first_workspace_option_is_the_same_as_defined_in_user_profile(e3270_special):
    user_profile = z.read_ds(dataset=f'{hlq}.UKOBDATF({username})')
    firstws = re.search(f'FIRSTWS=(\w+)', user_profile).group(1)
    d = e3270_special
    d(key=keys.HOME)
    d('e.p', key=keys.ENTER, timeout=30)
    assert e3270u.get_current_panel(d) == 'KOBPRFCL'
    e3270u.click_tab(' Session/Logon ', d=d)
    assert e3270u.get_current_panel(d) == 'KOBPRFSS'
    first_ws = d.find_all_by_label("First workspace to be displayed . .")[0]
    assert firstws == str(first_ws)


def test_prohibit_koblogon_as_the_first_workspace(e3270_special):
    d = e3270_special
    d(key=keys.HOME)
    d('e.p', key=keys.ENTER, timeout=30)
    assert e3270u.get_current_panel(d) == 'KOBPRFCL'
    e3270u.click_tab(' Session/Logon ', d=d)
    assert e3270u.get_current_panel(d) == 'KOBPRFSS'
    d.find_by_label("First workspace to be displayed . .")('KOBLOGON')
    d.find("BACK")('').enter()
    assert d.find('Multi-Tenancy KOBLOGON cannot be your first workspace')


# for ITE1: T_D5_Corp1 object group, contains DB2 V11 (IB1A, IBA3),T_D5_Corp2 object group, contains DB2 V12 (IC1A, ICA4).
# for ITE4: T_D5_Corp1 object group, contains DB2 V11 (IB1D, IBD3),T_D5_Corp1 object group, contains DB2 V11 (IC1D, ICD4).
def test_verify_superuser(e3270_special):
    d = e3270_special
    d(key=keys.HOME)
    d('n.d').enter()
    db2s = e3270u.get_column_list('DB2\nID', 4, d=d)
    if db2s:
        assert any(db2[1] == 'C' for db2 in db2s), 'super-user does not see all data'
        assert any(db2[1] == 'B' for db2 in db2s), 'super-user does not see all data'
    else:
        assert False, 'multi-user does not have data'


def test_verify_push_buttons_works_fine(e3270_special):
    d = e3270_special
    d(key=keys.HOME)
    d('n.d').enter()
    assert e3270u.get_current_panel(d) == 'KDPSTART'
    d.cursor = e3270u.get_cursor_on_first_row_in_column('DB2\nID', d=d)
    d('R').enter()
    d.find('OK')('').enter()
    d.enter()
    assert d.find('Fastpath navigation is prohibited') is None


def test_no_whats_new_for_new_user():
    util.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, 'notdefined_user', 'multi', ())
    ds = z.read_ds(f'{hlq}.UKOBDATF({username[:-1].upper()}B)')
    z.del_ds(f'{hlq}.UKOBDATF({username[:-1].upper()}B)')
    time.sleep(30)
    em = e3270u.logon_beacon(hostname, applid, username=username[:-1] + 'b', password=password)
    try:
        d = em.display
        assert e3270u.get_current_panel(d) != "KOBSSNEW"
        d(key=keys.HOME)
        d('h.w').enter()
        assert e3270u.get_current_panel(d) == "KOBHLDIR"
    finally:
        e3270u.close_beacon(em)
        zftp = ZFTP(hostname, username, password)
        zftp.upload_ds(text=ds, dest=f'{hlq}.UKOBDATF({username[:-1].upper()}B)')


def test_not_defined_user_can_only_logoff():
    util.set_security(hostname, username, password, rtes[rte]['rte_hlq'], rte, 'notdefined_user', 'multi', ())
    ds = z.read_ds(f'{hlq}.UKOBDATF({username[:-1].upper()}B)')
    z.del_ds(f'{hlq}.UKOBDATF({username[:-1].upper()}B)')
    time.sleep(30)
    em = e3270u.logon_beacon(hostname, applid, username=username[:-1] + 'b', password=password)
    try:
        d = em.display
        d(key=keys.HOME)
        for option in ['e', 'z', 'c', 'g', 'i', 'd', 'm', 'n', 's']:
            current_panel = e3270u.get_current_panel(d)
            d('n.' + option).enter()
            if option == 'e':
                d('n.h').enter()
                d('n.h').enter()
                assert d.find('Multi-Tenancy Definition Error')
            else:
                assert current_panel == e3270u.get_current_panel(d)
    finally:
        e3270u.close_beacon(em)
        zftp = ZFTP(hostname, username, password)
        zftp.upload_ds(text=ds, dest=f'{hlq}.UKOBDATF({username[:-1].upper()}B)')


def test_kobgroup_firstws_working_for_superuser(zosmf):
    """														
    https://jira.rocketsoftware.com/browse/OMBS-1407														
    Setting up user TS5813A as SUPER and changing group to OMEGCICS in KOBUSER member.														
    Checking if FIRSTWS KOBSCICS specified in KOBGROUP for OMEGCICS will be picked up by superuser logon.														
    Reverting changes made in KOBUSER member.														
    """
    rte_hlq = rtes[rte]['rte_hlq']
    input_file = f"{rte_hlq}.UKOBDATF(KOBUSER)"
    file_backup = zosmf.read_ds(input_file)
    try:
        required_setup = f'{username.upper()} GROUP:OMEGCICS SUPER:YES'
        text_to_change = re.sub(rf"{username.upper()}\s+GROUP:(\w+)\s+SUPER:\w+", required_setup, file_backup)
        zosmf.write_ds(input_file, text_to_change)
        em = e3270u.logon_beacon(hostname, applid, username, password)
        d = em.display
        d(key=keys.HOME)
        assert e3270u.get_current_panel(d) == 'KOBSCICS'
    finally:
        e3270u.close_beacon(em)
        zosmf.write_ds(input_file, file_backup)