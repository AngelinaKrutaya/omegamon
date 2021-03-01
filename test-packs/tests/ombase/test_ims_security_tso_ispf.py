import pytest

from taf.zos.py3270 import ISPF
from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from taf.af_support_tools import TAFConfig
from libs.ivtenv import rtes
from taf import logging

from libs.ds import Dataset_ext
from libs import utils
from libs.ite1ims import *


logger = logging.getLogger(__name__)
rte = os.environ.get('rte', 'ite1')

root = TAFConfig().testpack_root


def copy_clist(dir_):
    z = Dataset_ext(hostname, username, password)
    source_dir = os.path.join(root, 'resources', 'members', rte_name, 'clist', omegamon)
    dst = rtes[rte]['clist']
    src = os.path.join(source_dir, dir_)
    utils.upload_files_to_pds(z, src, dst)


@pytest.fixture(scope='function')
def tso_in_out(request):
    copy_clist('tso')
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(24, 80))
    ispf = ISPF(em, username=user, password=password)
    try:
        d = ispf.em.display
        d(key=keys.PF3)
        d(text=f"ALTLIB ACTIVATE APPL(CLIST) DA('{rtes[rte]['clist']}')", key=keys.ENTER)
        d(text='%KOI', key=keys.ENTER)
        assert d.find('LOGGING ONTO OMEGAMON/IMS VTAM APPLICATION UNDER TSO')
        d(key=keys.ENTER)

        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        assert d.find('ZMENU    VTT     OI-II')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
        d('ispf', key=keys.ENTER)
    finally:
        ispf.logoff()


@pytest.fixture(scope='function')
def ispf_in_out(request):
    copy_clist('ispf')
    user = username
    if hasattr(request, 'param'):    
        user = request.param

    em = Emulator(hostname, model=2, oversize=(24, 80))
    ispf = ISPF(em, username=user, password=password)
    try:
        d = ispf.em.display
        d('6', key=keys.ENTER)
        d(text=f"ALTLIB ACTIVATE APPL(CLIST) DA('{rtes[rte]['clist']}')", key=keys.ENTER)
        d('%KOI', key=keys.ENTER)
        assert d.find('OBSPF - INVOCATION MENU')

        appl = d.find_by_label('OBVTAM APPL  ==>')
        appl(text=applid, key=keys.NEWLINE)
        option = d.find_by_label('OPTION  ===>')
        option('2', key=keys.ENTER)

        d(user, keys.NEWLINE)
        d(password, keys.ENTER)

        assert d.find('ZMENU    VTS     OI-II')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
        d('X', key=keys.ENTER)
    finally:
        ispf.logoff()


def setup_module(module):
    utils.set_security(hostname, username, password,  rtes[rte]['rte_hlq'], rte, omegamon, 'basic',
                       ('KOISUPD', 'KOIRACFA'), stc_job)


#### TESTS


def check_icmd_panel(d, mess):
    d('t', key=keys.ENTER)
    assert d.find('KOITOOL')
    d('a', key=keys.ENTER)
    assert d.find('KOICONS')
    command = d.find('>OCMD               ')
    command('-ICMD /DIS DB ALL', key=keys.ENTER)
    assert d.find(mess)
    d(key=keys.PF3)
    d(key=keys.PF3)


def test_tso_logon(tso_in_out):
    d = tso_in_out
    assert d.find('ZMENU    VTT     OI-II')


def test_tso_icmd_authorized(tso_in_out):
    check_icmd_panel(tso_in_out, 'RC =  0')


@pytest.mark.parametrize('tso_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_tso_icmd_non_authorized(tso_in_out):
    check_icmd_panel(tso_in_out, 'RACF HAS DETERMINED THAT YOU ARE NOT AUTHORIZED')


######## ISPF


def test_ispf_logon(ispf_in_out):
    d = ispf_in_out
    assert d.find('ZMENU    VTS     OI-II')


def test_ispf_icmd_authorized(ispf_in_out):
    check_icmd_panel(ispf_in_out, 'RC =  0')


@pytest.mark.parametrize('ispf_in_out', [(username[:-1]+'b' if username.upper().endswith('A') else username+'b')],
                         indirect=True)
def test_ispf_icmd_non_authorized(ispf_in_out):
    check_icmd_panel(ispf_in_out, 'RACF HAS DETERMINED THAT YOU ARE NOT AUTHORIZED')
