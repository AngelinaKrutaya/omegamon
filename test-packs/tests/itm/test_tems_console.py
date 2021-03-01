import os
import requests
from html import unescape
import pytest

from libs.creds import *
from libs.ivtenv import rtes


rte = os.environ.get('rte', 'ite4')
hostname = rtes[rte]['hostname']
host_p = f"http://{rtes[rte]['hostname']}:{rtes[rte]['tems_http']}"
action = '/kdh/console/command.html'


def idfn(val):
    if isinstance(val, str):
        return f"command is  {val} "


question_mark_expected = [
    'res1: Display status of RES1 logical resource manager',
    'ras1: Manage RAS1 (Reliability, Availability, Serviceability)',
    'bss1: Manage BSS1 (Basic System Services)',
    'kde1: Manage KDE1 (Transport Services) component',
    'http: HTTP Server Management',
    'gateway: Manage Firewall Gateway',
    'csv1: Manage CSV1 (Contents Supervision)',
    'kdcstat: Display status of KDC (RPC Services) component',
    'kpx: Manage KPX (Remote Agent Proxy)',
    'kra: Manage KRA (Remote Agent Framework)',
]


def setup_module(module):
    pass


@pytest.fixture(scope='module')
def web_session():
    session = requests.Session()
    session.auth = (username, password)
    yield session
    r = session.get(host_p + action,
                    data={'command1': 'ras1 set ERROR'}
                    )




@pytest.mark.parametrize('command, result', [
    ('?', [
        'res1: Display status of RES1 logical resource manager',
        'ras1: Manage RAS1 (Reliability, Availability, Serviceability)',
        'bss1: Manage BSS1 (Basic System Services)',
        'kde1: Manage KDE1 (Transport Services) component',
        'http: HTTP Server Management',
        'gateway: Manage Firewall Gateway',
        'csv1: Manage CSV1 (Contents Supervision)',
        'kdcstat: Display status of KDC (RPC Services) component',
        'kpx: Manage KPX (Remote Agent Proxy)',
        'kra: Manage KRA (Remote Agent Framework)',
    ]),
    ('res1', ['Index', 'Page', 'Size', 'KBBAC_lab_t', 'KBBCR_ccb_t']),
    ('ras1 units', ['kdebswt.c', 'km3csag', 'tms630fp7', 'kbbcrr1.c', 'Default trace class(es):']),
    ('ras1 ctbld',
     ['Component code: khd', 'Component code: kge', 'Component code: ksh',
      'Component code: klb', 'Default trace class(es):']),
    ('ras1 set (UNIT:kbbcrcd ANY)', ['OK', 'Default trace class(es):']),
    ('ras1 list', [
        '00000001, Comp="KLX", Class=EVERYE+EVERYU+ER',
        '00000003, Comp="KDH", Class=EVERYE+EVERYU+ER',
        '00000005, Comp="KDE", Class=EVERYE+EVERYU+ER',
        '00000007, Comp="NCS", Class=EVERYE+EVERYU+ER',
        'Default trace class(es):',
    ]),
    ('ras1 log', ['KBB_RAS1=(UNIT:kbbcrcd ANY) is now in effect', 'Default trace class(es):']),
    ('bss1 dir', ['Positional argument required']),
    ('bss1 evaluate', ['Positional argument required']),
    ('bss1 config',
     ['Registered configuration variables:',
      'Config variable KDC_DEBUG = "N"',
      'Config variable KDE_DEBUG = "N"',
      'Config variable KDH_DEBUG = "N"',
      'Config variable KLX_DEBUG = "N"',
      'Config variable RES1_DEBUG = "NULL"',
      ]),
    ('bss1 info',
     [f'System Name: {hostname.upper()}', 'User Name: OMEGSTC', f"Task Name: {rtes[rte]['tems'].upper()}",
      'System Type: z/OS;02.04.00',
      'Effective User Name: OMEGSTC',
      ]),
    ('bss1 setenv F=9999', ['setenv: F="9999"']),
    ('bss1 getenv F', ['F="9999"']),
    ('bss1 listenv', ['KDS_VALIDATE', 'F(', ')="9999"', 'Total Variables:', 'Hash Efficiency:']),
    ('kde1 gskver', ['GSKit not active on z/OS']),
    ('kde1 status', ['Implementation Info:', 'Driver Info:', 'Network Info:', 'Families:', 'Interface Info:', 'ip.tcp:',
                     'Transport Parameters:', 'PORT:']),
    ('kde1 resolve rsd4', ["String: 'ip.pipe:#192.168.54.124'", "Name: 'ip.pipe:rsd4.rocketsoftware.com'"]),
    ('kra', ['Positional argument required']),
    ('kra status', ['Framework Status', 'Product Version:', 'Product Affinity:']),
    ('kra list', ['Registered Table List', 'Name: KS3.KS3RLLCKSD']),
    ('kra table KS3RLLCKSD', ['Table Display: KS3.KS3RLLCKSD']),
    ('kra requests', ['Positional argument required']),
    ('http', ['Driver:', 'Revision:', 'Inbound']),
    ('csv1 status', ['Entry manage_component, Service']),
    ('kdcstat', ['Driver: 1:']),
    ('kpx status', ['stubbed']),
], ids=idfn)
def test_tems_console(web_session, command, result):
    r = web_session.get(host_p + action,
                        data={'command1': command}
                        )
    # print(r.text)
    r_unescaped = unescape(r.text)
    for t in result:
        assert t in r_unescaped

