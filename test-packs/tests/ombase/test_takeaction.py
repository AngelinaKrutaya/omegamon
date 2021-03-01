import os
from taf import logging
from taf.zos.py3270 import keys
import libs.e3270utils as u
import libs.utils as utils
from libs.creds import *
from libs.ivtenv import rtes

rte = os.environ.get('rte', 'ite1')
hlq = rtes[rte]['rte_hlq']
hostname = rtes[rte]['hostname']
applid = rtes[rte]['tom_applid']
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

'''
def setup_module():
    rte1 = Parmgen(username, password, hlq[0:hlq.rfind('.')], rte)
    try:
        rte1.save_config()
        rte1.logon()
        rte1.change_parameters(params={'KDS_KMS_SECURITY_COMPATMD': 'N'})
        rte1.step_3_1_parse()
        rte1.step_4_12_copy_replace_files_from_wk()
    finally:
        rte1.restore_config()
        rte1.logoff()
'''


def test_for_cics(e3270_in_out):
    d = e3270_in_out
    u.click_tab(' CICS ')
    u.zoom_into_first_row('CICSplex\nName', 'S')
    u.zoom_into_first_row('CICS Region\nName', 'R')
    d('P').enter()
    assert u.get_current_panel(d) == 'KCPPRGS'
    # 'enabling' cics program is a 'takeaction' undercover.
    u.zoom_into_first_row('Program\nName', 'e')
    assert d.find('Take Action Results')
    # This error suits for us
    assert d.find("KCP0032E: OMEG HAS NOT BEEN INITIALIZED IN THE CICS ADDRESS\nSPACE") or \
           d.find('KCP4016I: The SET command has been sent to CICS.')


def test_for_mfn(e3270_in_out):
    d = e3270_in_out
    u.click_tab(' MFN ')
    assert u.get_current_panel(d) == 'KOBSMFN'
    d.find_by_label('Command ==>')('ping').enter()
    d.find_by_label('SMFID:')('RSD1')
    d.find_by_label('TCPIP STC:')('TCPIP')
    d.find_by_label('Hostname/IP Address:')('192.168.54.122')
    d.find_by_label('Source IP Address  :')('192.168.54.121').enter()
    assert u.get_current_panel(d) == 'KN3CRTS'
    assert d.find('Command Response')
    assert d.find('Ping #1 response took')


def test_for_mq(e3270_in_out):
    d = e3270_in_out
    u.click_tab(' MQ ')
    u.zoom_into_first_row('QMgr\nName')
    assert u.get_current_panel(d) == 'KMQQMSTS'
    d.find('Current Not Running').shift((0, 5))('', key=keys.ENTER)
    assert u.get_current_panel(d) == 'KMQCHNRS'
    # start channel is a 'takeaction'
    u.zoom_into_first_row('Channel\nName', '!')
    d('s').enter()
    assert d.find('MQ Command Successful')


def test_for_ims(e3270_in_out):
    d = e3270_in_out
    u.click_tab(' IMS ')
    u.zoom_into_first_row('IMS\nID')
    assert u.get_current_panel(d) == 'KIPHLTI'
    d('!').enter()
    # IMS Commander(ILOG)
    d('c').enter()
    assert u.get_current_panel(d) == 'KIPILOG'
    # generate fake command
    cmd = utils.get_random_alpha_numeric(5)
    # any command in the IMS log is a 'takeaction'. If we see this command in the refreshed log,
    # it means command has been sent successfully
    d.find_by_label('===>')(cmd).enter()
    d('').enter()
    assert d.find(cmd)
    assert d.find('CSLN046W The command contains an invalid verb or no client is registered for the verb.')


def test_for_mvs(e3270_in_out):
    d = e3270_in_out
    u.click_tab(' z/OS ')
    # sysplex data can be hijacked by other TEMS
    if d.find('Sysplex Data Unavailable'):
        d.find_by_label('Command ==>')('ZOSLPARS').enter()
        u.zoom_into_first_row('Sysplex\nName')
        d('z').enter()
        d('a').enter()
    else:
        u.zoom_into_first_row('Sysplex\nName')
        u.zoom_into_first_row('LPAR\nName')

    assert u.get_current_panel(d) == 'KM5ASPO'
    u.zoom_into_first_row('Address Space\nName', '!')
    # increasing time is a 'takeaction'
    d('t').enter()
    d('+', keys.NEWLINE)
    d('100', keys.NEWLINE)
    d('s').enter()
    # any response is ok as long as we get it
    assert d.find(regex='Request for job .* ASID .* submitted.') or \
           d.find('Not supported for address space type of:')
