import os
import re
import time
import pytest
from taf import logging
from taf.af_support_tools import TAFConfig
from taf.zos.common.dataset import Dataset
from taf.zos.py3270 import ISPF
from taf.zos.py3270 import Emulator
from taf.zos.zosmflib import zOSMFConnector
from libs.creds import *
from libs.ivtenv import rtes
from libs.e3270navigation import *
from taf.zos.py3270.display import LABEL_RIGHT
from libs.ivtenv import RteType

rte = os.environ.get('rte', 'ite1')
hlq = rtes[rte]['rte_hlq']
hostname = rtes[rte]['hostname']
applid = rtes[rte]['tom_applid']
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)
rte_hlq = rtes[rte]['rte_hlq']
user_profile = f"{rte_hlq}.UKOBDATF({username.upper()})"

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

TIMEOUT = 60


@pytest.fixture(scope='module')
def profile_backup_rest(zosmf):
    backup_profile = zosmf.read_ds(user_profile)
    yield
    zosmf.write_ds(user_profile, backup_profile)


def find_and_update_preferences(nav, textfind, labelposition, fieldupd, d):
    d(key=keys.HOME)
    d(nav, key=keys.ENTER, timeout=TIMEOUT)
    d.find_by_label(textfind, label_pos=labelposition)(fieldupd).enter()


def verify_values_in_profile(zosmf, required, d):
    d.find(' Save ').enter()
    d.find('Profile Save As').enter()
    verify_profile = zosmf.read_ds(user_profile)
    assert all(string in verify_profile for string in required)


def setup_module():
    # enable generic search for test_cics_filter_by_transaction
    z = zOSMFConnector(hostname, username, password)
    user_profile = f"{rtes[rte]['rte_hlq']}.UKOBDATF({username})"
    member_text = z.read_ds(user_profile)
    text_to_add = 'SET KCP_GENERIC_FIND=YES'
    if text_to_add not in member_text:
        member_text = member_text.replace('<CUADATA>', f'{text_to_add}\n<CUADATA>')
        z.write_ds(user_profile, member_text)


def check_notexist(d):
    d.find('Command ==> ').shift((0, 12))('=NOTEXIST', key=keys.ENTER)
    assert d.find('Could not locate Panel ID NOTEXIST')

    d(key=keys.HOME)
    d(key=keys.ENTER, timeout=TIMEOUT)
    assert not d.find('Could not locate Panel ID NOTEXIST')


def check_hub_hostname(d):
    hub_name = rtes[rte]['hub_name']
    # 4: to remove 'HUB_'
    assert d.find(f'Host {hub_name[4:].lower()}')
    assert not d.find('Host Unknown')


# TESTS-------------------------------------------------------------------------------


def test_nonexisting_panel_from_kobstart(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBSTART', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel() == 'KOBSTART'

    check_notexist(d)


def test_nonexisting_panel_from_kobstart_with_collapsed_table(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBSTART', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel() == 'KOBSTART'
    # sysplex data in first table is not always available as other RTE can hijack sysplex level.
    captions = 'Sysplex.*Average.*Highest'
    # first table is visible
    if d.find(regex=captions):
        # set cursor for collapsing first table
        d.cursor = 5, 2
        d(key=keys.ENTER)
        assert not d.find(regex=captions)
    # 1st table has no data and already collapsed
    else:
        assert d.find("Sysplex Data Unavailable: Enter 'ZOSLPARS' for LPAR Data")
    d.find('Command ==> ').shift((0, 12))('=NOTEXIST', key=keys.ENTER)
    assert d.find('Could not locate Panel ID NOTEXIST')
    d(key=keys.HOME)
    d(key=keys.ENTER, timeout=TIMEOUT)
    assert not d.find('Could not locate Panel ID NOTEXIST')


def test_nonexisting_panel_from_kcpstart(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.c', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel() == 'KCPSTART'

    check_notexist(d)


def test_nonexisting_panel_from_kcprgns(e3270_in_out):
    d = e3270_in_out
    cics_navigate_to_KCPRGNS(d)

    check_notexist(d)


def test_nonexisting_panel_from_kcprgno(e3270_in_out):
    d = e3270_in_out
    cics_navigate_to_KCPRGNS(d)
    u.zoom_in_regex('CICQ5|CIPP5', 'S')
    assert u.get_current_panel() == 'KCPRGNO'

    check_notexist(d)


def test_nonexisting_panel_from_kipstart(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.i', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel() == 'KIPSTART'

    check_notexist(d)


def test_nonexisting_panel_from_nodata_panel(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.g', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel() == 'KGWSTART'

    check_notexist(d)


def test_hide_odi(e3270_in_out):
    d = e3270_in_out
    d.find('«')('', key=keys.ENTER)
    assert d.find(regex='HUB.*RTE.*NAV.*ODI.*SIT')
    d(key=keys.HOME)
    d('hide odi', key=keys.ENTER, timeout=TIMEOUT)
    assert not d.find(regex='HUB.*RTE.*NAV.*ODI.*SIT')


def test_cics_filter_by_progname(e3270_in_out):
    def set_progname_DFHEMTD(e3270_in_out):
        d(key=keys.HOME)
        d('FIND', key=keys.ENTER, timeout=TIMEOUT)

        d.find('FIND PROGram      ').shift((0, 18))('DFHEMTD', key=keys.ENTER)
        assert d.find('CICS Regions with Program DFHEMTD installed')

    d = e3270_in_out
    cics_navigate_to_KCPRGNS(d)

    set_progname_DFHEMTD(d)

    # only one program name must be in column
    cics_and_program = set(u.get_column_list('Program\nName'))
    assert 'DFHEMTD' in cics_and_program and len(cics_and_program) == 1
    assert u.get_current_panel() == 'KCPPRGFP'

    d('', key=keys.PF4)
    d('1', key=keys.ENTER)
    assert d.find('Filter Detail')
    d('=', key=keys.NEWLINE)
    d('FRED', key=keys.ENTER)
    assert d.find('1. Program Name.................... =   FRED')
    u.click_tab(' OK ')
    # table must be empty, so first symbol is '>', means collapsed
    assert d.find(regex='> \ * CICS Regions with Program DFHEMTD installed \ * F4 Show Filters')
    d('', key=keys.PF3)
    set_progname_DFHEMTD(d)
    assert not d.find('F4 Show Filters')


def test_cics_filter_by_transaction(e3270_in_out):
    d = e3270_in_out
    cics_navigate_to_KCPRGNS(d)

    d(key=keys.HOME)
    d('FIND', key=keys.ENTER, timeout=TIMEOUT)

    d.find('FIND TRANsaction  ').shift((0, 18))('T*', key=keys.ENTER)
    if d.find('Generic search is not enabled!'):
        assert False, 'you need to add SET KCP_GENERIC_FIND=YES into UKOBDATF(<user>)'
    assert d.find('CICS Regions which install transactions as T*')
    assert u.get_current_panel() == 'KCPTRNFP'
    tran_list1 = u.get_column_list('Transaction\nID')

    d('', key=keys.PF4)
    d('1', key=keys.ENTER)
    assert d.find('Filter Detail')
    d('=', key=keys.NEWLINE)
    d('CI*', key=keys.ENTER)
    assert d.find('1. CICS Region Name................ =   CI*')
    u.click_tab(' OK ')
    tran_list2 = u.get_column_list('Transaction\nID')
    assert 0 < len(tran_list2) <= len(tran_list1)


def test_cics_menu_view_filter_is_available(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1319
    Verify that menu View/Filters is available on KCPRGNS screen
    :param e3270_in_out:
    :return:
    """
    d = e3270_in_out
    cics_navigate_to_KCPRGNS(d)

    d(key=keys.HOME)
    d('v.f', key=keys.ENTER, timeout=TIMEOUT)
    filters_menu = """  Filter(s)             
                        
1. CICS Region Name.....
2. CPU Utilization......
3. Transaction Rate.....
4. VTAM Applid..........
5. VTAM Generic Applid..
6. XCFGROUP.............
7. System ID............
                        
     Clear All Filters  """
    assert d.find(filters_menu)


# Every next navigation after leaving 'History' screen by pressing 'HOME' should not open a W/S in a 'HISTORY' mode.
def test_no_remaining_in_history_mod(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.m').enter()
    assert u.get_current_panel() == 'KMQSTART'
    assert d.find('QMgr\nName')
    d.find_by_label("Q\nN", label_pos="TOP")("H").enter()
    assert u.get_current_panel() == 'KMQQMSTH'
    # right tray may be open because of previous tests, so HOME button is not visible
    # close tray
    if d.find('»'):
        d.find('»').enter()
    d.find('HOME').enter()
    d.find(' IMS ').enter()
    assert not d.find('History')
    # go back to initial screen
    d.find(' Events ').enter()


# Some attributes not displayed during a scroll in the situation editor.
# In this test need to use 24:80 terminal screen.
def test_no_attributes_skipped_during_a_scroll():
    em = u.logon_beacon(hostname, applid, username, password, (24, 80))
    old_display = u.display
    u.display = em.display
    try:
        em.display(key=keys.HOME)
        em.display('e.s').enter()
        em.display.find_by_label('CICSPlex', label_pos="RIGHT")("s").enter()
        em.display('OMBS_303').enter()
        while not em.display.find('CICSplex BTS Activity Details'):
            em.display.find('Table Name')('', key=keys.PF8)
        em.display.find_by_label('CICSplex BTS Activity Details', label_pos="RIGHT")("s").enter()
        # close table
        em.display.find('×')('').enter()
        # find numbers of rows in the table
        pattern = 'Rows \s+(\d{1,3}) to \s+(\d{1,3}) of \s+(\d{1,3})'
        rows_from, rows_to, rows_of = [int(x) for x in re.search(pattern, str(em.display)).group(1, 2, 3)]
        attributes = u.get_column_list("Column Name", 10)
        while rows_to != rows_of:
            assert len(attributes) == rows_to
            em.display(key=keys.PF8)
            attributes += u.get_column_list("Column Name")
            rows_to = int(re.search(pattern, str(em.display)).group(2))
        assert len(set(attributes)) == rows_to
    finally:
        u.display = old_display
        u.close_beacon(em)


def test_help_for_filter_columns(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-954
    New help button in Filter Detail dialog
    """
    d = e3270_in_out
    u.click_tab(' DB2 ', d)
    assert u.get_current_panel(d) == 'KOBSDB2'
    # go to threads
    d('t').enter()
    assert u.get_current_panel(d) == 'KDPTHD52'
    # go to filters
    d('v.f').enter()
    assert d.find('Filter(s)')
    # go to Plan filter
    d('1').enter()
    assert d.find('Filter Detail')
    assert d.find('Help for Column')
    # click the button
    d.find('Help for Column').enter()
    # verify help
    assert d.find('Help associated with Plan')
    assert d.find('The name of an application plan that DB2 produces during')


@pytest.mark.parametrize("nav, panel", [
    ('n.e', 'KOBSITST'),
    ('=KOBSITMN', 'KOBSITMN'),
])
def test_autorefresh_several_panels(e3270_in_out, nav, panel):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1033
    Verify autorefresh
    """
    refresh_time = '020'
    autoupdate_label = 'Auto Update   :'
    d = e3270_in_out
    d(nav).enter()
    assert u.get_current_panel(d) == panel
    try:
        d.find_by_label(autoupdate_label)(refresh_time).enter()
        # check that interval entered correctly
        assert d.find_by_label(autoupdate_label).visible_only == refresh_time
        # save seconds from time
        _, old_time = u.get_date_time_from_screen(d)
        old_time = int(old_time.split(':')[2])
        time.sleep(int(refresh_time) + 2)
        _, new_time = u.get_date_time_from_screen(d)
        new_time = int(new_time.split(':')[2])
        # calculate expected seconds of new time
        expected_time = (old_time + int(refresh_time)) % 60
        # deviation is possible for 1 sec or 2 sec
        assert (new_time == expected_time or new_time == (expected_time + 1) % 60 or
                new_time == (expected_time + 2) % 60)
    finally:
        d.find_by_label(autoupdate_label)('Off').enter()


def test_provide_situation_status_tree_samples_focused_on_sme(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    current_panel = u.get_current_panel()
    count_words = len(d.find_all('CICS'))
    d('e.w').enter()
    assert u.get_current_panel() == 'KOBWIZ01'
    button = d.find_by_label('CICS', label_pos=LABEL_RIGHT)
    button('').enter()
    d.find('SAVE')('').enter()
    assert d.find('Profile Save As')
    d.enter()
    assert u.get_current_panel() == current_panel
    # If display has three words 'CICS' on screen. We exclude product 'CICS' from
    # situation tree and check that display has only two words 'CICS'. Else if display has two words
    # on screen without 'CICS' on sit tree. Then we include product 'CICS' and wait three words.
    if count_words == 3:
        assert len(d.find_all('CICS')) == 2
    elif count_words == 2:
        assert len(d.find_all('CICS')) == 3


def test_support_the_ability_to_offer_an_alternate_top_level_workspace(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    current_panel = u.get_current_panel()
    d('e.w').enter()
    assert u.get_current_panel() == 'KOBWIZ01'
    d.find('CICS')('').enter()
    d.enter()
    assert u.get_current_panel() == 'KOBWIZ01'
    button = d.find_by_label('Show CICS Regions', label_pos=LABEL_RIGHT)
    button('').enter()
    button = d.find_by_label('Use Custom', label_pos=LABEL_RIGHT)
    button('').enter()
    button = d.find_by_label('Show CICSplexes', label_pos=LABEL_RIGHT)
    button('').enter()
    assert d.find('All Active CICSplexes')
    d.find('SAVE')('').enter()
    assert d.find('Profile Save As')
    d.enter()
    assert u.get_current_panel() == current_panel


def test_workspace_kcprgns_not_display_issues(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1220
    Check that after multiple refreshes don't get a xx/s display in the "Stg. Violations last hour"
    column in the KCPRGNS workspace.
    """
    d = e3270_in_out
    cics_navigate_to_KCPRGNS(d)
    d.enter()
    d.enter()
    d.enter()
    column = u.get_column_list('Stg. Violations last hour', width=25)
    for row in column:
        assert not re.search(r'/s', row)


def test_request_to_show_month_and_day_in_the_center_display_button(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1152
    Check to show Month and Day in the center “Display” Button in KDPSUBSM workspace.
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.d').enter()
    assert u.get_current_panel() == 'KDPSTART'
    u.zoom_into_first_row('DB2\nID', 'H')
    assert u.get_current_panel(d) == 'KDPSTRTH'
    u.zoom_into_first_row('Recording Time', 's')
    assert u.get_current_panel(d) == 'KDPSUBSM'
    assert d.find(regex=r'BACK|\s+\d{2}:\d{2}\s←\s+\d{2}\s[Jan,Feb,Mar,Apr,May,Jun,Jul,Aug,Sep,Oct,Nov,Dec]\s\d{2}[:]'
                        r'\d{2}\s+→')


@pytest.mark.parametrize("x,y", [(24, 80), (32, 80)])
def test_check_redesign_history_configuration_workspaces_for_24_and_32_line_screens(x, y):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1227
    """
    em = u.logon_beacon(hostname, applid, username, password, (x, y))
    old_display = u.display
    u.display = em.display
    d = em.display
    try:
        d(key=keys.HOME)
        d('v.h').enter()
        assert u.get_current_panel() == 'KOBHISTL'
        d.find_by_label('OMEGAMON for CICS on z/OS', label_pos=LABEL_RIGHT)('s').enter()
        assert u.get_current_panel() == 'KOBHISTB'
        d.find_by_label('CICSplex Overview', label_pos=LABEL_RIGHT)('s').enter()
        assert u.get_current_panel() == 'KOBHISN1'
        assert d.find('OK')
        d.find('Distribution')('').enter()
        # create collection, if collection doesn't exist
        if u.get_current_panel() != 'KOBHISN2':
            d.find_by_label('Collection Name')('collection')
            d.find_by_label('Interval')('s').enter()
            d.find('OK').enter()
            d.find('The collection was successfully created.')
            d.find('Distribution')('').enter()
        assert u.get_current_panel() == 'KOBHISN2'
    finally:
        u.display = old_display
        u.close_beacon(em)


def test_popup_with_hash(e3270_in_out, jes):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1300
    Hash sign was interpreted in popup as an ISPF special character for changing color.
    So # itself was skipped.
    :param e3270_in_out: fixture
    :param jes: fixture
    :return:
    """
    job_name = 'IVT#HASH'
    d = e3270_in_out
    # go to db2
    d(key=keys.HOME)
    d('n.d').enter()
    assert u.get_current_panel() == 'KDPSTART'
    # get a name of the first db2
    first_db2 = u.get_column_list('DB2\nID', width=4, d=d)[0]
    # submit a long select with # in a job name
    job = jes.submit_jcl(path_relative=True, path='resources/jobs/db2thd.jcl',
                         params={'{ssid}': first_db2, '{job}': job_name}, wait=False)
    try:
        time.sleep(10)
        # zoom into thread details and click on job name to get a popup
        u.zoom_in(first_db2, 't', d=d)
        # plan name is dsntep2
        u.zoom_in('DSNTEP2', 's', d=d)
        # get popup
        d.find(job_name).enter()
        assert d.find(job_name)
    finally:
        job.cancel()


def test_db2_dsnzparm_find_underscore_is_honored(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1311
    Verify that _ is not translated to space in the FD command in command line
    """
    d = e3270_in_out
    db2_param = 'MAXSORT_IN_MEMORY'
    u.click_tab(' DB2 ', d)
    assert u.get_current_panel(d) == 'KOBSDB2'
    # go to dsnzparm
    d('g').enter()
    assert u.get_current_panel(d) == 'KDPZSYS'
    u.click_tab(' STG ', d)
    d.find_by_label('Command ==>')(f'fd "{db2_param}"').enter()
    assert not d.find('*Bottom of data reached*')

    y, x = u.get_text_position(f'{db2_param}')
    highlighting = d[y, x + 1].highlighting
    assert 'REVERSE' in highlighting


def test_no_none_option_in_ispf_preference(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1394
    Checking if there is no NONE option in ispf preferences. Also did additional checks for available options.
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('e.p', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel(d) == 'KOBPRFCL'
    u.click_tab(' ISPF ', d)
    assert u.get_current_panel(d) == 'KOBPRFIS'
    assert not d.find('NONE')
    assert d.find('(FULL/LINE)')
    d.find_by_label('Support  . . . . . . .')('LINE').enter()
    assert d.find('Support  . . . . . . . LINE  (FULL/LINE)')
    d.find_by_label('Support  . . . . . . .')('FULL').enter()
    assert d.find('Support  . . . . . . . FULL  (FULL/LINE)')
    d.find_by_label('Support  . . . . . . .')('ABCD').enter()
    assert d.find('Support  . . . . . . . FULL  (FULL/LINE)')


def test_ability_to_use_html_zoom(e3270_in_out, zosmf):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1402
    Copy IVTHTML panel to UKANWENU. After that check if we are able to
    navigate to KOBWENUS panel using zoom.
    """

    root = TAFConfig().testpack_root
    ivthtml = 'IVTHTML'
    mem_path = os.path.join(root, 'resources', 'members', 'panels', f'{ivthtml.lower()}')
    rte_hlq = rtes[rte]['rte_hlq']
    target_mem = f"{rte_hlq}.UKANWENU({ivthtml})"
    source_file = open(f'{mem_path}', 'r')
    read_text = source_file.read()
    zosmf.write_ds(target_mem, read_text)
    d = e3270_in_out
    d(key=keys.HOME)
    d(f'={ivthtml}', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel(d) == f'{ivthtml}*'
    d.find('OMBS-1402').enter()
    assert u.get_current_panel(d) == 'KOBWENUS'


def test_prompt_for_profile_save_as_added_in_FirstWorkspace(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1406
    Checking if saving changes in Edit -> First Workspace user gets prompt for "Profile Save As"
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('e.w', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel(d) == 'KOBWIZ01'
    d.find('SAVE').enter()
    assert d.find('Profile Save As')


def test_checking_KOBTREEZ_KOBTREET_member_update(zosmf):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1411
    Checking if QI product code is added to KOBTREEZ member and verifying other required product codes.
    Checking if WebSphere|QI parameter is added to KOBTREET member and verifying other required parameters.
    """
    rtetype = rtes[rte]['type']
    if rtetype == RteType.SHARED:
        rte_hlq = rtes[rte]['shared_ds']
    else:
        rte_hlq = rtes[rte]['rte_hlq']
    verification_file = f"{rte_hlq}.RKANEXEC(KOBTREEZ)"
    member_data = zosmf.read_ds(verification_file)
    required_text = ["MSPRODCODE = 'CP'", "MSPRODCODE = 'C5'", "MSPRODCODE = 'OMCICS'", "MSPRODCODE = 'IP'",
                     "MSPRODCODE = 'I5'", "MSPRODCODE = 'DP'", "MSPRODCODE = 'D5'", "MSPRODCODE = 'M5'",
                     "MSPRODCODE = 'N3'", "MSPRODCODE = 'MQ'", "MSPRODCODE = 'JJ'",
                     "MSPRODCODE = 'S3'", "MSPRODCODE = 'GW'", "MSPRODCODE = 'QI'"]
    assert all(string in member_data for string in required_text)
    verification_file2 = f"{rte_hlq}.RKANWENU(KOBTREET)"
    member2_data = zosmf.read_ds(verification_file2)
    required_text2 = ['(Tivoli Enterprise Monitoring Server|All Managed Systems)',
                      '{"aff":"CICSPlex"}', '{"aff":"CICSTG"}', '{"aff":"MVS DB2"}', '{"aff":"IMS"}',
                      'Java Virtual.', '(MQSER|Queue)', '(Mainframe Net|VTAM|TCP/IP|NCP)',
                      '{"aff":"Storage Subsystem"}', '{"aff":"MVS Sys.*"}', '{"aff":"Warehouse Proxy"}',
                      '(z/VM Linux Systems|Linux OS)', '(WebSphere|QI)']
    assert all(string2 in member2_data for string2 in required_text2)


@pytest.mark.parametrize("nav, textfind, labelposition, fieldupd, required", [
    # Colors tab tests
    ('=KOBPRFCL', 'Box Lines . . . . .', 'LEFT', 'Green', ['BOXLINES=Green']),
    ('=KOBPRFCL', 'Panel ID  . . . . .', 'LEFT', 'Yellow', ['PANELID=Yellow']),
    ('=KOBPRFCL', 'Action Bar . . . . . .', 'LEFT', 'White', ['ACTIONBAR=White']),
    ('=KOBPRFCL', 'Panel Trailer  . . . .', 'LEFT', 'White', ['TRAILER=White']),
    # Status tab tests
    ('=KOBPRFST', 'Good/OK . . . . . .', 'LEFT', 'White', ['OKGOOD=White']),
    ('=KOBPRFST', 'Warning/Caution  . . .', 'LEFT', 'White', ['WARNING=White']),
    ('=KOBPRFST', '00 Missing', 'LEFT', 'Yellow', ['RANGE0=Yellow']),
    ('=KOBPRFST', '01 OK/Good', 'RIGHT', 'Y', ['RANGE0RV=Y']),
    ('=KOBPRFST', '06 Minor', 'LEFT', 'Red', ['RANGE6=Red']),
    ('=KOBPRFST', '07 Critical', 'RIGHT', 'N', ['RANGE6RV=N']),
    # Session/Logon tab tests
    ('=KOBPRFSS', "First workspace to be displayed . .", 'LEFT', 'KOBSCICS', ["FIRSTWS=KOBSCICS"]),
    ('=KOBPRFSS', "First NAV1 Plex-level Value . . . .", 'LEFT', 'KOBSZOS', ["FIRSTNAV1=KOBSZOS"]),
    ('=KOBPRFSS', "First NAV2 System-level Value . . .", 'LEFT', 'KOBSDB2', ["FIRSTNAV2=KOBSDB2"]),
    ('=KOBPRFSS', "Show \"What's New\" at session start.", 'LEFT', 'Y', ["SHOWLOGONMSG=Y"]),
    ('=KOBPRFSS', "Engage Trace at session start . . .", 'LEFT', 'Y', ["TRACE=Y"]),
    ('=KOBPRFSS', "Global Query Timeout Value  . . . .", 'LEFT', '010', ["MAXTIMEOUT=010"]),
    # History tab test
    ('=KOBPRFHS', '1. M Historical Last', 'RIGHT', '1', ['HISTOPTION=1']),
    ('=KOBPRFHS', '1. M Historical Last', 'LEFT', '033', ['HISTLMINS=033']),
    ('=KOBPRFHS', "2. H Historical Last", 'LEFT', '001', ["HISTLHOUR=001"]),
    # ISPF tab tests
    ('=KOBPRFIS', "Tab to action bar choices . . . . .", 'LEFT', 'N', ["ISPFTABABAR=N"]),
    ('=KOBPRFIS', "Tab to point-and-shoot fields . . .", 'LEFT', 'N', ["ISPFTABPNTS=N"]),
    ('=KOBPRFIS', "APL Graphics Support  . . . . . . .", 'LEFT', 'LINE', ["APLGRAPHICS=LINE"]),
    ('=KOBPRFIS', "Make '/' default Summary Action . .", 'LEFT', 'Y', ["ACTDEFAULT/=Y"]),
    # Date/Time tab tests
    ('=KOBPRFDT', "Date begins with  . :", 'LEFT', 'DD', ["DATEFORMAT=DD"]),
    ('=KOBPRFDT', "Date separator  . . :", 'LEFT', '.', ["DATESEP=."]),
    ('=KOBPRFDT', "Time clock format . :", 'LEFT', '12', ["TIMEFORMAT=12"]),
    ('=KOBPRFDT', "Time separator  . . :", 'LEFT', '.', ["TIMESEP=."]),
    # Auto/Update tab tests
    ('=KOBPRFAU', "Auto Update Frequency . . . . . . .", 'LEFT', '150', ["AUTOUPDATE=150"]),
    ('=KOBPRFAU', "Auto Update Suspend Cycle Count . .", 'LEFT', '2990', ["AUTOSUSPEND=2990"]),
    # Hub check tab tests
    ('=KOBPRFHB', "Hub Check when no data displayed  .", 'LEFT', '7', ["HUBCHECKCYCLE=7"]),
    ('=KOBPRFHB', "Limit Hub Check to Auto/Update  . .", 'LEFT', 'N', ["HUBCHECKAONLY=N"]),
    # Filters tab tests
    ('=KOBPRFFI', "Show Filter values in column headers . .", 'LEFT', 'Y', ["SHOWFILTERS=Y"]),
    # JESPrint tab tests
    ('=KOBPRFJS', "Screen Print DDNAME . :", 'LEFT', 'TS5813A', ["JESDDPRINT=TS5813A"]),
])
def test_edit_preferences_various_tab_updates(profile_backup_rest, zosmf, e3270_in_out, nav, textfind, labelposition,
                                              fieldupd, required):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1431
    Taking a backup of TS5813A user profile.
    Updating all tabs present in Edit -> Preferences, verifying if changes were applied.
    Loading back user TS5813A profile.
    """
    find_and_update_preferences(nav, textfind, labelposition, fieldupd, e3270_in_out)
    verify_values_in_profile(zosmf, required, e3270_in_out)


def test_check_if_screen_not_missing_in_cicsplex_resource_views():
    """
    https://jira.rocketsoftware.com/browse/OMBS-1112
    Launching a session in 24x80.
    Navigating to KCPHLP20 panel and zooming in "New CICSplex Resource Views"
    Verifying if all required screens appear in KCPH2005 panel.
    """
    em = u.logon_beacon(hostname, applid, username, password, (24, 80))
    d = em.display
    try:
        d(key=keys.HOME)
        d('=KCPHLP20', key=keys.ENTER, timeout=TIMEOUT)
        d.find('New CICSplex Resource Views').enter()
        assert u.get_current_panel(d) == 'KCPH2005'
        assert 'MQ active requests' in str(d[8, :])
        assert 'which regions a particular library dataset' in str(d[22, :])
        d(key=keys.PF8)
        assert 'Region Storage Violations' in str(d[4, :])
        assert 'Umbrella Data in Task History' in str(d[22, :])
        d(key=keys.PF8)
        assert 'Umbrella Data in Task History' in str(d[4, :])
        assert 'the limit to alleviate a potential' in str(d[21, :])
        d(key=keys.PF8)
        assert 'CICS Exit information' in str(d[4, :])
        assert 'It is now possible to view details' in str(d[15, :])
    finally:
        u.close_beacon(em)


# Must be the last ones


def test_host_field_on_kobhub04_with_new_user_profile():
    # del user profile in TOM
    z = Dataset(hostname, username, password)
    rte_hlq = rtes[rte]['rte_hlq']
    username_logon = username[:-1] + 'b' if username.upper().endswith('A') else username + 'b'

    z.del_ds(f'{rte_hlq}.UKOBDATF({username_logon})')
    em = u.logon_beacon(hostname, applid, username_logon, password)
    old_display = u.display
    u.display = em.display
    try:
        d = em.display

        hub_name = rtes[rte]['hub_name']
        max_hub_chars = 16
        assert u.get_current_panel() == 'KOBHUB01'
        # taken from test_situations::switch_hub()
        d.find(regex='CANCEL   NEXT').shift((0, 10))('', key=keys.ENTER)
        if d.find('Press Enter key to get the list of Hubs'):
            d.find(regex=r'>\s+Press Enter key to get the list of Hubs')('').enter()
        if len(hub_name) <= max_hub_chars:
            u.zoom_in(hub_name, 'S')
        else:
            table_y, _ = d.find('Hub Name   ').x
            # last line in case new user
            end_y, _ = d.find(regex=' No Hubs in Use ').x
            areas1 = [area.x[0] for area in d.find_all(hub_name[0:max_hub_chars]) if table_y < area.x[0] < end_y]
            d.find('Hub Name   ')('', key=keys.PF11)
            areas2 = [area.x[0] for area in d.find_all(hub_name[max_hub_chars:] + ' ') if table_y < area.x[0] < end_y]
            y = list(set(areas1).intersection(areas2))[0]
            d.cursor = y, 3
            d('S', key=keys.ENTER)
        d('1', key=keys.ENTER)
        assert u.get_current_panel() == 'KOBHUB04'
        check_hub_hostname(d)
        d.find('OK   SAVE').shift((0, 6))('', key=keys.ENTER)
        d.find('EXIT   NEXT').shift((0, 1))('', key=keys.ENTER)
        assert u.get_current_panel() == 'KOBSEVTS'
    finally:
        u.display = old_display
        u.close_beacon(em)


def test_host_field_on_kobhub03_from_hub_command(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('hub', key=keys.ENTER, timeout=TIMEOUT)
    assert u.get_current_panel() == 'KOBHUB03'
    check_hub_hostname(d)


def test_host_field_on_kobhub03_from_hub_button(e3270_in_out):
    d = e3270_in_out
    # open tray
    d.find('«').enter()
    d.find(regex='»⎸HUB ').shift((0, 3)).enter()
    assert u.get_current_panel() == 'KOBHUB03'
    check_hub_hostname(d)


def test_whats_new_for_framework(e3270_in_out):
    d = e3270_in_out
    d(key=keys.HOME)
    d('h.w').enter()
    assert u.get_current_panel() == 'KOBHLDIR'
    assert d.find('Multi-Tenancy')
    assert d.find('Security Logging')


# In this test need to use 24:80 terminal screen.
def test_history_configuration_distribution_list_multi_selection_loop_after_scroll():
    em = u.logon_beacon(hostname, applid, username, password, (43, 80))
    old_display = u.display
    u.display = em.display
    d = em.display
    try:
        d(key=keys.HOME)
        d('v.h').enter()
        assert u.get_current_panel() == 'KOBHISTL'
        d.find_by_label('OMEGAMON for CICS on z/OS', label_pos=LABEL_RIGHT)('s').enter()
        assert u.get_current_panel() == 'KOBHISTB'
        d.find_by_label('CICSplex Overview', label_pos=LABEL_RIGHT)('s').enter()
        assert u.get_current_panel() == 'KOBHISN1'
        d.find('Distribution')('').enter()
        # create collection, if collection doesn't exist
        if u.get_current_panel() != 'KOBHISN2':
            d.find_by_label('Collection Name')('collection')
            d.find_by_label('Interval')('s').enter()
            d.find('OK').enter()
            d.find('The collection was successfully created.')
            d.find('Distribution')('').enter()
        assert u.get_current_panel() == 'KOBHISN2'
        d(key=keys.PF8)
        d.cursor = u.get_cursor_on_first_row_in_column('∨', number_cell=5)
        u.shift_cursor()
        x, y = d.cursor
        while '───' not in str(d[x:x + 1, y:y + 3]):
            d('s')
            u.shift_cursor(direction='bottom')
            u.shift_cursor(direction='left')
            x, y = d.cursor
        d.enter()
        assert d.find('Including')
    finally:
        u.display = old_display
        u.close_beacon(em)


def test_no_incorrect_message_on_r_selection_after_navigate_to_db2(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-854
    """
    d = e3270_in_out
    try:
        for i in range(2):
            d(key=keys.HOME)
            d('n.d').enter()
            u.zoom_in('IC1A', 'R')
            assert u.get_current_panel(d) == 'KDPHFIL1'
            d.find('OK').enter()
            assert u.get_current_panel(d) == 'KDPHISTL'
    except:
        assert d.find('No Records Found Matching Selection Criteria')
        d.enter()


def test_using_search_command_no_changed_number_of_lines_displayed(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1161
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.c').enter()
    u.zoom_into_first_row('CICSplex\nName', 'S')
    u.zoom_into_first_row('CICS Region\nName', 'R')
    d('P').enter()
    assert u.get_current_panel(d) == 'KCPPRGS'
    number_of_rows = len(u.get_column_list('Program\nName'))
    d.find_by_label('Command ==>')(f'search IXM4C57').enter()
    d(key=keys.PF7)
    assert len(u.get_column_list('Program\nName')) == number_of_rows


def test_check_events_tab_header_text(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1160
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBSEVTS').enter()
    assert d.find('OMEGAMON Products')


def test_multi_tenancy_tenant_switching_error_message(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1190
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBMTCON').enter()
    d.find('Tenant').enter()
    assert d.find('You must select both a Customer and a Group in order to\nemulate being a Tenant')
    d.find('OK').enter()


def test_multi_tenancy_switching_check_customers(e3270_in_out, zosmf):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1190
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBMTCON').enter()
    text = zosmf.read_ds(dataset=f'{hlq}.UKOBDATF(KOBCUST)')
    omegs_all_cust = []
    omegs_one_cust = []
    # get omegamons and msl_names from KOBCUST
    for omegamon, msl_name, sign in re.findall(r'\n(.*?)="(.*?)"(.*)', text):
        omegs_one_cust.append((omegamon, msl_name))
        if not sign:
            omegs_all_cust.append(omegs_one_cust)
            omegs_one_cust = []
    counter = 0
    # get customers and custname from KOBCUST, compare their with e3270 UI
    for customer, custname in re.findall(r'CUSTOMER:(\S+),\nCUSTNAME:"(.*?)",', text):
        assert d.find(regex=f'{customer}.*?{custname}')
        u.zoom_in(customer, 's')
        for omegamon, msl_name in omegs_all_cust[counter]:
            assert d.find(regex=f'{omegamon}.*?{msl_name}')
        counter += 1
        d.find('BACK').enter()
    d.find('Cancel').enter()


def test_multi_tenancy_switching_check_groups(e3270_in_out, zosmf):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1190
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBMTCON').enter()
    d.find('Groups').enter()
    text = zosmf.read_ds(dataset=f'{hlq}.UKOBDATF(KOBGROUP)')
    # get groups, first workspaces, signs showing omegamons ws or not and compare with e3270 UI
    for group, firstws in re.findall(r'GROUP:(.*?),FIRSTWS=(\w+),', text):
        om_line_first, om_line_second = re.search('GROUP:' + group + ',FIRSTWS=\w+,(\n\S+)(\n\S+)', text).group(1, 2)
        nav = [m.group(2) for m in re.finditer("(SHOW\w+)=(\w)", om_line_first + om_line_second)]
        navigation = '.*?'.join(nav)
        assert d.find(regex=f'{group}.*?{firstws}.*?{navigation}')
    d.find('Cancel').enter()


def test_multi_tenancy_switching_check_users(e3270_in_out, zosmf):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1190
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBMTCON').enter()
    d.find('Users').enter()
    text = zosmf.read_ds(dataset=f'{hlq}.UKOBDATF(KOBUSER)')
    # get users, descriptions from KOBUSER and compare their with e3270 UI
    for user, group, is_super, customer in re.findall(r'USERID:(\w+)\s+GROUP:(\w+)\s+SUPER:(\w+)\s+CUSTOMER[:=](\w+)',
                                                      text):
        if is_super == 'YES':
            assert d.find(regex=f'{user}.*?{customer}.*?{group}.*?Super')
        elif is_super == 'NO':
            assert d.find(regex=f'{user}.*?{customer}.*?{group}.*?Tenant')
    d.find('Customers').enter()
    d.find('Cancel').enter()


def test_multi_tenancy_tenant_switching(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1190
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('=KOBMTCON').enter()
    customer_name = u.get_column_list('Customer\nName', width=45)[0]
    u.zoom_into_first_row('◇Customer')
    u.zoom_into_first_row('OMEGAMON')
    d.find('BACK').enter()
    d.find('Groups').enter()
    # append value in dict -> 'omegamons' to show omegamon product or not
    omegamons = {'Events': '', 'z/OS': '', 'CICS': '', 'C/TG': '', 'IMS': '', 'DB2': '', 'MQ': '', 'MFN': '',
                 'STOR': '', 'JVM': ''}
    cursor = u.get_cursor_on_first_row_in_column('◇Group')
    is_show_omegamons = d[cursor[0]:cursor[0] + 1, :].replace(' ', '').split('│')
    count = 2
    for name in omegamons:
        while len(is_show_omegamons[count]) < 1:
            count += 1
        omegamons[name] = is_show_omegamons[count]
        count += 1
    u.zoom_into_first_row('◇Group')
    d.find('BACK').enter()
    # switch to tenant mode
    d.find('Tenant').enter()
    d.find('OK').enter()
    assert d.find(regex=rf'{customer_name}\s+⎹«⎸\s+TENANT')
    # check showing subpanels with names omegamons on KOBSEVTS ws
    for omegamon, is_show in omegamons.items():
        if "Y" in is_show:
            assert d.find(regex=rf'│\s+{omegamon}\s+│')
        else:
            assert not d.find(regex=rf'│\s+{omegamon}\s+│')
    # check that omegamons navigations are allowed
    for nav in ['n.e', 'n.z', 'n.c', 'n.g', 'n.i', 'n.d', 'n.m', 'n.n', 'n.s']:
        d(key=keys.HOME)
        current_panel = u.get_current_panel(d)
        d(nav).enter()
        assert u.get_current_panel(d) != current_panel
    # check that file, views, edit, tools pulldowns are not allowed
    for nav in ['f.o', 'e.s', 'e.o', 'e.w', 'v.f', 'v.s', 'v.w', 'v.h', 'v.r', 't.a', 't.u', 't.h', 't.p', 't.s', 't.d',
                't.e', 't.g', 't.v', 't.o', 't.f']:
        d(key=keys.HOME)
        current_panel = u.get_current_panel(d)
        d(nav).enter()
        assert u.get_current_panel(d) == current_panel
    # check that button RTE is not allowed
    d.find('«')('').enter()
    assert not d.find('RTE')
    d(key=keys.HOME)
    d('=KOBMTCON').enter()
    # switch back to Super user
    d.find('Super').enter()
    d.find('OK').enter()
    assert not d.find(regex=rf'{customer_name}\s+⎹«⎸\s+TENANT')


def test_e3270_session_not_terminates_after_selecting_an_option(e3270_in_out):
    """
    https://jira.rocketsoftware.com/browse/OMBS-1291

    Select DB SSID. Use / selecting one of the buffer pools. Then session should not terminate.
    """
    d = e3270_in_out
    d(key=keys.HOME)
    d('n.d').enter()
    assert u.get_current_panel(d) == 'KDPSTART'
    u.zoom_into_first_row('DB2\nID')
    assert u.get_current_panel(d) == 'KDPSUBSM'
    d.find('BP')('').enter()
    u.zoom_into_first_row('◇Name')
    assert u.get_current_panel(d) == 'KDPBPD54'


def test_run_omegamon_z_os_tso_KOMCLSTE_without_abend():
    '''
    https://jira.rocketsoftware.com/browse/OMBS-1457

    Omegamon z/OS TSO KOMCLSTE does not have abend S0C4-04 KOBAS510 after running.
    It is reproduced only on ite4.
    '''
    em = Emulator('rsd4', model=2, oversize=(24, 80))
    ispf = ISPF(em, username=username, password=password)
    rte = 'ite4'
    try:
        d = ispf.em.display
        d.find_by_label('===>')('=xall').enter()
        d.find('READY')
        abend = 'OB0933 OMEGAMON resource cleanup initiated for abend S0C4  RC=00000004'
        d(f"exec '{rtes[rte]['rte_hlq']}.RKANSAMU(KOMCLSTE)'").enter()
        assert not d.find(abend)
        d('', key=keys.PF3)
        d.find('READY')
        d(f"exec '{rtes[rte]['rte_hlq']}.RKANSAMU(KOMCLIST)'").enter()
        assert not d.find(abend)
    finally:
        ispf.em.disconnect()
        ispf.em.close()
