import pytest
from taf.af_support_tools import Config as TafConfig
from taf.zos.py3270 import ISPF
from taf.zos.py3270 import X3270
from taf.zos.py3270 import keys

# Getting credentials from test-packs/tests/config/config.ini
c = TafConfig('config.ini')
py3270_hostname = c.get_option('py3270', 'py3270_hostname')
username = c.get_option('zos_credentials', 'username')
password = c.get_option('zos_credentials', 'password')

target = py3270_hostname

em_list = [X3270]

cmd_list = ['/s JOB1', 
            '/p JOB2', 
            '/c JOB3',
            ]

ds_mask_list = ['QLFR.**',
                'QLFR.**.**',
                ]


# A fixture returning an ISPF object which is then passed to application fixtures
@pytest.fixture(scope='module', params=em_list)
def ispf(request):
    em = request.param(target=target)
    ispf = ISPF(em, username=username, password=password)
    yield ispf
    ispf.logoff()


# Fixtures returning ISPFPanel objects for SDSF, DSLIST and TSO features
@pytest.fixture(scope='module')
def sdsf(ispf):
    sdsf = ispf.start('s.da')
    yield sdsf
    sdsf.exit()


@pytest.fixture(scope='module')
def dslist(ispf):
    dslist = ispf.start('3.4')
    yield dslist
    dslist.exit()


@pytest.fixture(scope='module')
def tso(ispf):
    tso = ispf.start('6')
    yield tso
    tso.exit()


@pytest.mark.parametrize("cmd", cmd_list)
def test_issue_SDSF_cmds(sdsf, cmd):
    sdsf(cmd)
    assert sdsf.find('COMMAND ISSUED')


@pytest.mark.parametrize("ds_mask", ds_mask_list)
def test_list_ds(dslist, ds_mask):
    ds_entry = dslist.find_by_label('Dsname Level . . .')
    ds_entry(text=ds_mask, key=keys.ENTER)
    assert not dslist.find('No data set names found')
    dslist(key=keys.PF3)


# Test can also be parametrized through a fixture:
@pytest.fixture(scope='module', params=['time', 'time'])
def tso_cmd(request):
    yield request.param


def test_issue_tso_commands(tso, tso_cmd):
    cmd_entry = tso.find_by_label('===>')
    cmd_entry(text=tso_cmd, key=keys.ENTER)
    assert not tso.find(regex='COMMAND .* NOT FOUND')
    tso(key=keys.PF3)
