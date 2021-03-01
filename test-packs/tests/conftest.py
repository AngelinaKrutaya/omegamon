import pytest
from _pytest.mark.structures import Mark
import libs.e3270utils as u
from libs import utils
from taf.zos.jes import JESAdapter
from taf.zos.zosmflib import zOSMFConnector
from libs.parmgen import Parmgen
from libs.creds import *

@pytest.fixture(scope='module')
def e3270_in_out(request):
    mod = request.module
    em = u.logon_beacon(mod.hostname, mod.applid, mod.username, mod.password)
    try:
        u.display = em.display
        yield em.display
    finally:
        u.close_beacon(em)


@pytest.fixture(scope='module')
def logon_to_parmgen(request):
    mod = request.module
    rte = Parmgen(mod.username, mod.password, mod.hlq[0:mod.hlq.rfind('.')], mod.rte)
    try:
        rte.logon()
        yield rte.d
    finally:
        rte.logoff()


@pytest.fixture(scope='module')
def go_to_config(logon_to_parmgen):
    d = logon_to_parmgen
    d.find_by_label('===>')('2').enter()
    d.find_by_label('===>')('1').enter()
    d.enter()
    yield d


@pytest.fixture(scope='function', autouse=True)
def auto_back(request):
    def auto_back_teardown():
        if 'ombase' in request.session.name:
            if request.module.__name__ in ['test_regression', 'test_situations', 'test_takeaction']:
                if request.node.name in (
                        'test_host_field_on_kobhub04_with_new_user_profile',
                        'test_no_attributes_skipped_during_a_scroll',
                        'test_history_configuration_distribution_list_multi_selection_loop_after_scroll',
                        'test_checking_KOBTREEZ_KOBTREET_member_update',
                        'test_run_omegamon_z_os_tso_KOMCLSTE_without_abend',
                        'test_check_if_screen_not_missing_in_cicsplex_resource_views'):
                    return
                if 'test_check_redesign_history_configuration_workspaces_for_24_and_32_line_screens' in request.node.name:
                    return
                assert not u.display.find('Program Check')
                u.back_to_ZMENU()
            elif request.module.__name__ in ['test_zos_regression_classic', ]:
                assert not request.module.display.find('Program Check')
                utils.back_to_ZMENU(request.module.display)

    request.addfinalizer(auto_back_teardown)


@pytest.hookimpl(trylast=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    rep = outcome.get_result()
    test_failed = item.session.testsfailed
    if 'test_no_super_user_cannot_get_access_to_any_member_of_rte' in rep.nodeid and rep.when == "setup" and rep.skipped == True:
        for item in item.session.items:
            if 'test_multi.py' in item.nodeid:
                item.own_markers.append(Mark(name='skip', args=(), kwargs={}))


@pytest.fixture(scope='module')
def jes(request):
    mod = request.module
    jes = JESAdapter(mod.hostname, mod.username, mod.password)
    return jes


@pytest.fixture(scope='module')
def zosmf(jes):
    return jes.zo

