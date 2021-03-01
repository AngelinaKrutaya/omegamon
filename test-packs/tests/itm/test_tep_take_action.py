import os
import pytest
import time
from taf.zos.zosmflib import zOSMFConnector
from taf import logging
from taf.zos.jes import JESAdapter
import time
import keyboard
import threading
from taf.zos.py3270 import ISPF
from taf.zos.py3270.ispf import Menu
from taf.zos.py3270 import Emulator
from concurrent.futures.thread import ThreadPoolExecutor
from taf.zos.py3270 import keys
import asyncio
import pytest



from libs.pyjubula import *
from libs.tep.tep import TEP

from libs.creds import *
from libs.ivtenv import rtes
from taf.zos.zosmflib import zOSMFConnector

logger = logging.getLogger(__name__)
logging.getLogger().setLevel(logging.INFO)

# jubula_agent = 'localhost'
jubula_agent = 'localhost'
host_teps = 'WALDEVITMZQA03'
hostname = 'RSD4'
plex = 'RSPLEXL4'
rte = 'ite4'
tep = None

jubula_agent = os.environ.get('jubula_agent', jubula_agent) + ':60000'
hostname = os.environ.get('hostname', hostname)
plex = os.environ.get('plex', plex).upper()

z = zOSMFConnector(hostname, username, password)

# we need base username (not ends with 'a') as it has an auth for $kobsec class
username = os.environ.get('mf_user', username[:-1])
password = os.environ.get('mf_password', password)
host_teps = os.environ.get('host_teps', host_teps)

tems = rtes[rte]['tems'].upper()

clean_racf_cmds = [
    f'RDELETE $KOBSEC ({tems}.KGLUMAP.*)',
    f'RDELETE $KOBSEC ({tems}.KGLUMAP.TS5813)',
    f'RDELETE $KOBSEC ({tems}.KGLUMAP.TS*)',

    f'RDELETE $KOBSEC ({tems}.KGLCMAP.*)',
    f'RDELETE $KOBSEC ({tems}.KGLCMAP.%LU)',

    f'rdelete $kobsec ({tems}.KDS_VALIDATE)',

]

start_trace = f'F {tems},CTDS TRACE ADD FILTER ID=TK1 UNIT=KGL CLASS(ALL)'

stop_trace = f'F {tems},CTDS TRACE REMOVE FILTER ID=TK1'

racf_refresh_cmd = '\nsetropts raclist($kobsec) refresh\n'

# racf_clean_all = racf_refresh_cmd.join(clean_racf_cmds) + racf_refresh_cmd

kglumap = rtes[rte]['rte_hlq'] + '.RKANPARU(KGLUMAP)'


def execute_racf_cmd(cmds):
    racf_cmd = '\n'.join(cmds) + racf_refresh_cmd
    job = jes.submit_jcl(path_relative=True, path='resources/jobs/tso.jcl',
                         params={'{cmd}': racf_cmd}, wait=True)


@pytest.fixture(scope='module')
def tep():
    tep = TEP(jubula_agent, host_teps, classes_dir='C:/AUT_WD', username=username, password=password)
    yield tep
    #tep.logoff()

jes = JESAdapter(hostname, username, password)
def setup_module():
    z.issue_command(start_trace)
    execute_racf_cmd(clean_racf_cmds)
    jes.zo.del_ds(kglumap)

def teardown_module():
    z.issue_command(stop_trace)
    log = get_log()
    f = open('log.txt', 'w')
    f.write(log)

def get_log():
    stc_job_id = ''
    for job, data in z.list_jobs(prefix=rtes[rte]['tems'], owner='OMEGSTC').items():
        if data['status'] == 'ACTIVE':
            stc_job_id = job
    log = z.get_file(jobname=rtes[rte]['tems'], jobid=stc_job_id, section='RKLVLOG')
    return log

def do_take_action(tep):
    node_path = ['MVS Operating System', 'RSPLEXL4:RSD4:MVSSYS', 'Address Space Overview']
    cr = tep.navigate_to_node(node_path)
    cr.select_popup_by_text('Take Action.../Select...')
    ta_combo_box_mapping = ["javax.swing.JComboBox", "javax.swing.JComboBox",
                            ["frame2", "javax.swing.JDialog_1", "javax.swing.JRootPane_1", "null.layeredPane",
                             "null.contentPane", "javax.swing.JPanel_1", "javax.swing.JPanel_2",
                             "javax.swing.JScrollPane_1", "javax.swing.JViewport_1", "javax.swing.JPanel_1",
                             "candle.kjr.swing.MessageSenderPanel_1", "javax.swing.JPanel_1",
                             "candle.kjr.swing.MessageChooserPanel_1", "javax.swing.JComboBox_1"],
                            ["javax.swing.JLabel_1", "javax.swing.JLabel_2", "javax.swing.JPanel_1",
                             "javax.swing.JScrollPane_1"]]
    ta_combo_box = ComboBoxComponent('TA Box', ta_combo_box_mapping, tep.aut)
    ta_combo_box.select_entry_by_text('IVT_MVS_TA_LU_Lower')
    ta_ok_button_mapping = ["javax.swing.AbstractButton", "javax.swing.JButton",
                            ["frame2", "javax.swing.JDialog_1", "javax.swing.JRootPane_1", "null.layeredPane",
                             "null.contentPane", "javax.swing.JPanel_1", "javax.swing.JPanel_1",
                             "javax.swing.JButton_1"],
                            ["javax.swing.JButton_1", "javax.swing.JButton_2"]]
    ta_ok_button = ButtonComponent('TA OK', ta_ok_button_mapping, tep.aut)
    ta_ok_button.click()
    time.sleep(15)
    ta_ok_button.click()
    ta_ok_button.click()
    while True:
        try:
            if keyboard.is_pressed('enter'):
                break
            time.sleep(1)
        except:
            break



@pytest.yield_fixture(scope='module')
def ispf():
    em = Emulator(hostname, model=2, oversize=(62, 160))
    ispf = ISPF(em, username=username, password=password)
    sdsf = ispf.start('s.log')
    d = sdsf.emulator.display()
    yield d
    ispf.logoff()

@pytest.yield_fixture
def loop():
    # Настройка
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop

    # Очистка
    loop.close()


def test_no_kglumap_no_racf_profile(tep,ispf):
    do_take_action(tep)
    d=ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
   # assert d.find('USER=OMEGSTC  NAME=OMEGAMON STCS')


def test_define_racf_profile_and_kglumap_with_read_access(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.*) uacc(none)","permit ITE4DS.KGLUMAP.* acc(read) class($KOBSEC) ID(omegstc)"])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=OMEGSTC  NAME=OMEGAMON STCS')

def test_kglumap_read_access_with_kglcmap_uacc_none(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.*) uacc(none)","permit ITE4DS.KGLUMAP.* acc(read) class($KOBSEC) ID(omegstc)",
                      "rdefine $kobsec (ITE4DS.KGLCMAP.*) uacc(none)"])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813  NAME=OMEGAMON STCS')

def test_kglumap_read_access_with_kglcmap_uacc_read(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.*) uacc(none)","permit ITE4DS.KGLUMAP.* acc(read) class($KOBSEC) ID(omegstc)",
                      "rdefine $kobsec (ITE4DS.KGLCMAP.*) uacc(none)","ralter $kobsec (ITE4DS.KGLCMAP.*) uacc(READ)"])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813  NAME=OMEGAMON STCS')


def test_kglumap_with_appldata_field_racf_userid(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.*) uacc(none)","permit ITE4DS.KGLUMAP.* acc(read) class($KOBSEC) ID(omegstc)"
                         ,"RALTER $KOBSEC ITE4DS.KGLUMAP.*  APPLDATA('TS5813B')",])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813B  NAME=OMEGAMON STCS')

def test_kglumap_tep_userid_with_empty_appldata(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.TS5813) uacc(READ)",])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813  NAME=OMEGAMON STCS')
    #run situation for this

def test_kglumap_tep_userid_with_appldata_racf_userid(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.TS5813) uacc(READ)",
                      "RALTER $KOBSEC ITE4DS.KGLUMAP.TS5813  APPLDATA('TS5813A')",])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813A  NAME=OMEGAMON STCS')

def test_kglumap_tep_userid_prefix_with_appldata_field_racf_userid(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.TS*) uacc(READ) APPLDATA('TS5813M')",])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813M  NAME=OMEGAMON STCS')

def test_kglumap_read_access_with_kglcmap_read_for_racf_userid(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLCMAP.*) uacc(none)", "ralter $kobsec (ITE4DS.KGLCMAP.*) uacc(READ)",
                      "permit ITE4DS.KGLCMAP.* acc(read) class($KOBSEC) ID(TS5813)"])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813  NAME=OMEGAMON STCS')

def test_kglcmap_uacc_none_upper_case_command(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLCMAP.%LU) uacc(None)",])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    #not allowed


#tep with user ts5813B
#def test_kglumap_tep_userid_with_appldata_racf_userid_run_under_another_tep_userid():
 #   execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLUMAP.TS5813) uacc(READ)",
 #                     "RALTER $KOBSEC ITE4DS.KGLUMAP.TS5813  APPLDATA('TS5813A')",])
    #not allowed


def test_kglcmap_uacc_read_upper_case_command_for_racf_userid(tep,ispf):
    do_take_action(tep)
    execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLCMAP.%LU) uacc(None)",
                      "permit ITE4DS.KGLCMAP.%LU acc(read) class($KOBSEC) ID(TS5813A)",])
    d = ispf
    go_down = d.find_by_label('===>')
    go_down('m', keys.PF8, 10)
    while d.find(regex=r'USER=\S+  NAME=') is None:
        d('', keys.PF7, 10)
    assert d.find('USER=TS5813A  NAME=OMEGAMON STCS')

#def test_situation():
 #   execute_racf_cmd(["rdefine $kobsec (ITE4DS.KGLCMAP.%LU) uacc(None)",
 #                     "permit ITE4DS.KGLCMAP.%LU acc(read) class($KOBSEC) ID(TS5813A)", ])
# TextComponent('Hub Time', hub_time_mapping, aut)

# app.click
# cr.select_popup_by_text(node_path)


############################################################################################################################################################


# PLEX

# @pytest.mark.tepdsg
# def test_DB2plex_node():
#     navigate_to_node('DB2plex')
#     check_ws('DB2plex Summary')
#
# @pytest.mark.tepdsg
# @pytest.mark.skip(reason="in our env this wks is empty, need somehow to switch to another variant of it")
# def test_DB2_node_dsg():
#     navigate_to_node('DB2')
#     check_ws('DB2 Systems Summary')
#
# @pytest.mark.tepdsg
# def test_Monitored_Systems_Summary():
#     navigate_to_node('Monitored Systems Summary')
#     check_ws('Monitored Systems Summary')
#


# @pytest.mark.tepdsg
# def test_Global_Lock_Conflicts():
#     lockWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'MODE=LC;LOCKTIME=120'}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     try:
#         navigate_to_node('Global Lock Conflicts')
#         time.sleep(10)
#         navigate_to_subnode_on_condition('Global Lock Conflicts','Global Lock Conflict Table View','Thread Locks Owned', 'Lock Status', 'Waiter')
#         check_ws('Thread Locks Owned')
#         navigate_to_node('Global Lock Conflicts')
#         #navigate_to_subnode_on_condition('Global Lock Conflicts','Global Lock Conflict Table View','Thread Locks Owned', 'Lock Status', 'Owner')
#         #check_ws('Thread Locks Owned')
#         #navigate_to_node('Global Lock Conflicts')
#         check_ws('Global Lock Conflicts')
#     finally:
#         setIRLMTimeout(user, password, sys, ssid)
#
# @pytest.mark.tepdsg
# def test_Coupling_Facility_Structures():
#     navigate_to_node('Coupling Facility Structures')
#     check_ws('Coupling Facility Structures')
#     navigate_to_subnode('Coupling Facility Structures','Coupling Facility Structures Table View','Coupling Facilities Connections')
#     check_ws('CF Connections')
#
# @pytest.mark.tepdsg
# def test_Group_Buffer_Pool_Structures():
#     navigate_to_node('Group Buffer Pool Structures')
#     check_ws('Group Buffer Pool Structures')
#     navigate_to_subnode('Group Buffer Pool Structures','Group Buffer Pool Structures Table View','Group Buffer Pool Connections')
#     check_ws('Group Buffer Pool Connections')
#
# @pytest.mark.tepdsg
# def test_Group_Buffer_Pool_Statistics():
#     navigate_to_node('Group Buffer Pool Statistics')
#     check_ws('Group Buffer Pool Statistics')
#     navigate_to_subnode('Group Buffer Pool Statistics','Group Buffer Pool Statistics Table View','Detailed GBP Statistics')
#     check_ws('Detailed Group Buffer Pool Statistics')
#
# @pytest.mark.tepdsg
# def test_Object_Analysis_Database(oa):
#     multipleWorkloadExecutionDB2WKL("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'2m', 'workloads':['LongRunningSelectWorkload','BufferpoolWorkload']}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Object Analysis Database')
#     check_ws('Object Analysis Database')
#     #navigate_to_subnode('Object Analysis Database','Object Analysis Database Table View','Object Analysis Spacename')
#     navigate_to_subnode_on_condition('Object Analysis Database','Object Analysis Database Table View','Object Analysis Spacename','Database Name','DSNDB01')
#     check_ws('Object Analysis Spacename')
#     navigate_to_subnode('Object Analysis Spacename','Object Analysis Spacename Table View','Object Analysis Spacename Detail Report')
#     check_ws('Object Analysis Spacename Detail Report')
#
# @pytest.mark.tepdsg
# def test_Group_Object_Analysis_Thread_Database(oa):
#     multipleWorkloadExecutionDB2WKL("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'2m', 'workloads':['LongRunningSelectWorkload','BufferpoolWorkload']}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Group Object Analysis Thread Database')
#     check_ws('Group Object Analysis Thread Database')
#     navigate_to_subnode_on_condition('Group Object Analysis Thread Database','Group Object Analysis Thread Database Table View','Group Object Analysis Thread Spacename','Database','OMPEWKL')
#     check_ws('Group Object Analysis Thread Spacename')
#     navigate_to_subnode('Group Object Analysis Thread Spacename','Group Object Analysis Thread Spacename Table View','Group Object Analysis Thread Spacename Detail')
#     check_ws('Group Object Analysis Thread Spacename Detail')
#
# @pytest.mark.tepdsg
# def test_Group_Object_Analysis_Database(oa):
#     multipleWorkloadExecutionDB2WKL("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'2m', 'workloads':['LongRunningSelectWorkload','BufferpoolWorkload']}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Group Object Analysis Database')
#     check_ws('Group Object Analysis Database')
#     navigate_to_subnode_on_condition('Group Object Analysis Database','Group Object Analysis Database Table View','Group Object Activity by Spacename','Database','OMPEWKL')
#     check_ws('Group Object Analysis by Spacename')
#     navigate_to_subnode('Group Object Analysis by Spacename','Group Object Activity by Spacename Table View','Group Object Activity by Spacename Detail')
#     check_ws('Group Object Analysis by Spacename Detail')
#
# @pytest.mark.tepdsg
# def test_Group_Object_Analysis_Volume_Thread(oa):
#     multipleWorkloadExecutionDB2WKL("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'5m', 'workloads':['LongRunningSelectWorkload','BufferpoolWorkload']}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Group Object Analysis Volume Thread')
#     check_ws('Group Object Analysis Volume Thread')
#     navigate_to_subnode('Group Object Analysis Volume Thread','Group Object Analysis Volume Thread Table View','Group Object Analysis Volume Thread Detail')
#     check_ws('Group Object Analysis Volume Thread Detail')
#
# @pytest.mark.tepdsg
# def test_Group_Object_Analysis_Volume(oa):
#     multipleWorkloadExecutionDB2WKL("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'5m', 'workloads':['LongRunningSelectWorkload','BufferpoolWorkload']}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Group Object Analysis Volume')
#     check_ws('Group Object Analysis Volume')
#     navigate_to_subnode_on_condition('Group Object Analysis Volume','Group Object Analysis Volume Table View','Group Object Analysis Volume Database','DB2 I/O Percent','100.0')
#     check_ws('Group Object Analysis Volume Database Report')
#     navigate_to_subnode('Group Object Analysis Volume Database Report','Group Object Analysis Volume Database Report Table View','Group Object Analysis Volume Spacename')
#     check_ws('Group Object Analysis Volume Spacename')
#     navigate_to_subnode('Group Object Analysis Volume Spacename','Group Object Analysis Volume Spacename','Group Object Analysis Volume Detailed Spacename')
#     check_ws('Group Object Analysis Volume Spacename Detail')
#
#
#
# ############################################################################################################################################################
#
# #Single
#
# @pytest.mark.one
# @pytest.mark.tepsingle
# def test_DB2_node_single():
#     navigate_to_node('DB2')
#     check_ws('DB2 Systems Summary')
#
# @pytest.mark.tepsingle
# def test_DB2_node_summary():
#     navigate_to_node('DB2-full-path')   #this is node with the name like QCA3:RS27:DB2
#     check_ws('DB2 Summary')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity():
#     navigate_to_node('Thread Activity')
#     check_ws('Thread Activity by Plan')
#     navigate_to_subnode('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail')
#     check_ws('Thread Detail')
#
# @pytest.mark.tepsingle
# def test_Storage_Consumption():
#     global db2ver
#     navigate_to_node('Storage Consumption')
#     check_ws('Storage Consumption')
#     navigate_to_subnode('Storage Consumption','MVS Storage','DB2 MVS Storage')
#     check_ws('MVS Storage Below 2 GB')
#     #rows in DBM1 MVS Storage Below 2 GB table sometimes are not visible w/o resizing, so we will use Agent table for zooming
#     navigate_to_subnode('MVS Storage Below 2 GB','Agent System Storage','MVS Storage Above 2 GB') #+ Common Storage , DB2 IRLM Storage
#     check_ws('MVS Storage Above 2 GB')
#     navigate_to_subnode('MVS Storage Above 2 GB','MVS Storage Above 2 GB','Common Storage') #+ DB2 IRLM Storage
#     check_ws('Common Storage')
#     if db2ver > 10:
#             navigate_to_subnode('Common Storage','Common Storage Below 2 GB','DB2 IRLM Storage')
#             check_ws('DB2 IRLM Storage')
#
#
# @pytest.mark.tepsingle
# def test_System_Status():
#     navigate_to_node('System Status')
#     check_ws('System Status')
#
# @pytest.mark.tepsingle
# def test_Subsystem_Management():
#     navigate_to_node('Subsystem Management')
#     check_ws('System Resource Manager (Subsystem)')
#
# @pytest.mark.tepsingle
# def test_Log_Manager():
#     navigate_to_node('Log Manager')
#     check_ws('System Resource Manager (Log)')
#
# @pytest.mark.tepsingle
# def test_EDM_Pool():
#     navigate_to_node('EDM Pool')
#     check_ws('System Resource Manager (EDM)')
#     navigate_to_subnode('System Resource Manager (EDM)','EDM Statistics','EDM Pool (DB2 V' + str(db2ver) + ')')
#     check_ws('EDM Pool')
#
# @pytest.mark.tepsingle
# def test_Buffer_Pool_Management():
#     navigate_to_node('Buffer Pool Management')
#     check_ws('Buffer Pool Management')
#     navigate_to_subnode('Buffer Pool Management','Buffer Pool Management','Buffer Pool Detail')  #better to check all rows, need new function
#     check_ws('Buffer Pool Detail')
#
#
# @pytest.mark.tepsingle
# def test_Volume_Activity(oa):
#     multipleWorkloadExecutionDB2WKL("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'2m', 'workloads':['LongRunningSelectWorkload','BufferpoolWorkload']}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Volume Activity')
#     check_ws('Volume Activity')
#
# @pytest.mark.tepsingle
# @pytest.mark.skipif(cics == 'NONE', reason="no cics")
# def test_CICS_Connections():
#     navigate_to_node('CICS Connections')
#     check_ws('CICS Connections')
#     navigate_to_subnode('CICS Connections','CICS Connections Summary','CICS Thread Details')
#     check_ws('CICS Threads')
#
# @pytest.mark.tepsingle
# @pytest.mark.skipif(ims == 'NONE', reason="no ims")
# def test_IMS_Connections():
#     navigate_to_node('IMS Connections')
#     check_ws('IMS Connections')
#     if ims != '':
#         imsBatchWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m', 'imsid':'{}'}}".format(user, password, sys, ssid, ims))
#         time.sleep(60)
#         navigate_to_subnode_on_condition('IMS Connections','IMS Connections','IMS Region Information', 'IMS Name', ims)   #TEP doesn't show info on control region, need workload
#         check_ws('IMS Region Information')
#
# @pytest.mark.tepsingle
# def test_DB2_Connect_Server():
#     navigate_to_node('DB2 Connect Server')
#     check_ws('DB2 Connect Server')
#     navigate_to_subnode('DB2 Connect Server','DB2 Connect Server','DB2 Connect\/Gateway Statistics') #+ Task List, Performance, Package Statistics
#     check_ws('DB2 Connect/Gateway Statistics')
#     navigate_to_subnode('DB2 Connect/Gateway Statistics','DB2 Connect Information','Tasks List') #+ Performance, Package Statistics
#     check_ws('Tasks List')
#     navigate_to_subnode('Tasks List','DB2 Connect Information','Package Statistics')
#     check_ws('Package Statistics')
#
#
#
# #WITH Workload
#
# @pytest.mark.tepsingle
# def test_Lock_Conflicts():
#     lockWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'MODE=LC;LOCKTIME=320'}}".format(user, password, sys, ssid, wkl_machine))
#     try:
#         navigate_to_node('Lock Conflicts')
#         check_ws('Lock Conflicts')
#         navigate_to_subnode_on_condition('Lock Conflicts','Local Lock Conflicts Table View','Thread Locks Owned', 'Lock Status', 'Waiter')
#         check_ws('Thread Locks Owned')
#     finally:
#         setIRLMTimeout(user, password, sys, ssid)
#
# @pytest.mark.tepsingle
# def test_Utility_Jobs():
#     utilityWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m'}}".format(user, password, sys, ssid))
#     navigate_to_node('Utility Jobs')
#     check_ws('Utility Jobs')
#
#
# @pytest.mark.tepsingle
# def test_Detailed_Thread_Exception():
#     id = longRunningSelect("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'minutes=3'}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(10)
#     navigate_to_node('Detailed Thread Exception')
#     check_ws('Detailed Thread Exceptions')    # DDF Statistics link requires workload
#     navigate_to_subnode_on_condition('Detailed Thread Exceptions','Detailed Thread Exceptions','DDF Statistics', 'Correlation ID', 'db2wkl' + id)
#     #navigate_to_subnode_on_condition('Detailed Thread Exceptions','Detailed Thread Exceptions','DDF Statistics', 'Plan Name', 'DISTSERV')
#     check_ws('DDF Statistics')
#
# #HTML Links
#
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_All_thd_connected():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(1)
#     check_ws('All Threads Connected to DB2')
#
# @pytest.mark.tepsingle
# @pytest.mark.skipif(cics == 'NONE', reason="no cics")
# def test_Thread_Activity_html_CICS_threads():
#     # cicsWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m', 'applids':'{}'}}".format(user, password, sys, ssid, cics))
#     run_workload('WorkloadRun.xml', 'RunCICSBatchLNS', "{{'user':'{}','password':'{}', 'hostname':'{}','ssid':'{}','duration':'3m','cics':'{}'}}".format(user, password, sys, ssid, cics))
#     time.sleep(30)
#     navigate_to_node('Thread Activity')
#     time.sleep(10)
#     sendTabsAndEnter(2)
#     time.sleep(10)
#     check_ws('CICS Thread Summary')
#     navigate_to_subnode_on_condition('CICS Thread Summary','CICS Thread Summary','Thread Detail','Plan','CICSLNS')
#
#     #column regexp for "Connection ID", changing to cics name
#     r_tmp = mappings["Thread Detail"]["Thread ID"]["Columns"][1][2][1]
#     mappings["Thread Detail"]["Thread ID"]["Columns"][1][2][1] = '^'+cics+'$'
#     time.sleep(10)
#     check_ws('Thread Detail')
#     mappings["Thread Detail"]["Thread ID"]["Columns"][1][2][1] = r_tmp
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Detailed_thd_exceptions():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(3)
#     check_ws('Detailed Thread Exceptions')
#
# #DOESNT WORK, NEEDS WORKLOAD
# @pytest.mark.tepsingle
# @pytest.mark.skip(reason="no workload is setuped")
# def test_Thread_Activity_html_Distributed_allied_thd():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(4)
#     check_ws('Distributed Allied Thread Summary')
#
# @pytest.mark.one
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_DBAT():
#     id = longRunningSelect("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'minutes=3 db2options ClientApplicationInformation=LongRunningSelectWorkload'}}".format(user, password, sys, ssid, wkl_machine))
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(5)
#     check_ws('DBAT End-to-End SQL Monitoring')
#     navigate_to_subnode_on_condition('DBAT End-to-End SQL Monitoring','Distributed Database Access Thread Summary','Distributed Thread Detail','Transaction ID','LongRunningSelectWorkload')
#     check_ws('Distributed Thread Detail')
#     navigate_to_subnode('Distributed Thread Detail','Thread ID ','Distributed Thread SQL Statistics')
#     check_ws('Distributed Thread SQL Statistics')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Enclave():
#     id = longRunningSelect("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'minutes=3 db2options ClientApplicationInformation=LongRunningSelectWorkload'}}".format(user, password, sys, ssid, wkl_machine))
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(6)
#     check_ws('Enclave Thread Summary')
#     navigate_to_subnode_on_condition('Enclave Thread Summary','Enclave Thread Summary','Enclave Information for a Thread','Plan','DISTSERV')
#     check_ws('Enclave Information for a Thread')
#     navigate_to_subnode('Enclave Information for a Thread','Service Period Information','Thread Enclave Service Period Information')
#     check_ws('Thread Enclave Service Period Information')
#
# @pytest.mark.tepsingle
# @pytest.mark.skipif(ims == 'NONE', reason="no ims")
# def test_Thread_Activity_html_IMS_threads():
#     imsBatchWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m', 'imsid':'{}'}}".format(user, password, sys, ssid, ims))
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(7)
#     check_ws('IMS Thread Summary')
#
#     dict_new = {'Connection ID':ims}
#     dict_old = update_regexp('Thread Detail', 'Thread ID', dict_new)
#
#     navigate_to_subnode_on_condition('IMS Thread Summary','IMS Thread Summary','Thread Detail','Plan','SQLBMP90')
#     check_ws('Thread Detail')
#     update_regexp('Thread Detail', 'Thread ID', dict_old)
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Lock_Conflicts():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     lockWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'MODE=LC;LOCKTIME=120'}}".format(user, password, sys, ssid, wkl_machine))
#     try:
#         sendTabsAndEnter(8)
#         check_ws('Lock Conflicts')
#         #navigate_to_subnode_on_condition('Lock Conflicts','Local Lock Conflicts Table View','Thread Locks Owned', 'Lock Status', 'Waiter')
#         #check_ws('Thread Locks Owned')
#     finally:
#         setIRLMTimeout(user, password, sys, ssid)
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Packages():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
#     sendTabsAndEnter(9)
#     check_ws('Thread Activity by Package')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Plans():
#     navigate_to_node('Utility Jobs')
#     time.sleep(30)
#     sendTabsAndEnter(10)
#     check_ws('Thread Activity by Plan')
#     navigate_to_subnode('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail')
#     check_ws('Thread Detail')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Utility_Jobs():
#     utilityWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m'}}".format(user, password, sys, ssid))
#     navigate_to_node('Thread Activity')
#     time.sleep(10)
#     sendTabsAndEnter(10)
#     check_ws('Utility Jobs')
#
#
# #HTML links from Thread Details
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_Distributed_Thread_Detail():
#     id = longRunningSelect("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'minutes=3 db2options ClientApplicationInformation=LongRunningSelectWorkload'}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(30)
#     navigate_to_node('Thread Activity')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'DISTSERV')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(0)
#     check_ws('Distributed Thread Detail')
#     navigate_to_subnode('Distributed Thread Detail','Thread ID ','Distributed Thread SQL Statistics')
#     check_ws('Distributed Thread SQL Statistics')
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_Thread_Wait_Events():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
# #    navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'DGO.*')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'KO2PLAN')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(1)
#     check_ws('Thread Wait Events')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_html_Thread_Enclave_Detail():
#     id = longRunningSelect("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'4m', 'wklOptions':'minutes=4 db2options ClientApplicationInformation=LongRunningSelectWorkload'}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(30)
#     navigate_to_node('Thread Activity')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'DISTSERV')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(2)
#     check_ws('Enclave Information for a Thread')
#     navigate_to_subnode('Enclave Information for a Thread','Service Period Information','Thread Enclave Service Period Information')
#     check_ws('Thread Enclave Service Period Information')
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_Plans():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
# #    navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'DGO.*')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'KO2PLAN')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(3)
#     check_ws('Thread Activity by Plan')
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_SQL1():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
# #    navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'DGO.*')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'KO2PLAN')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(4)
#     check_ws('Thread SQL Counts 1')
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_SQL2():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
# #    navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'DGO.*')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'KO2PLAN')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(5)
#     check_ws('Thread SQL Counts 2')
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_SQL3():
#     navigate_to_node('Thread Activity')
#     time.sleep(30)
# #    navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'DGO.*')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Plan', 'KO2PLAN')
#     check_ws('Thread Detail')
#     sendTabsAndEnter(6)
#     check_ws('Thread SQL Counts 3')
#
#
# @pytest.mark.tepsingle
# def test_Thread_Detail_html_Thread_Locks_Owned():
#     lockWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'3m', 'wklOptions':'MODE=LC;LOCKTIME=120'}}".format(user, password, sys, ssid, wkl_machine))
#     try:
#         time.sleep(10)
#         navigate_to_node('Thread Activity')
#         navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Thread Status', 'WAIT-LOCK')
#         check_ws('Thread Detail')
#         sendTabsAndEnter(7)
#         check_ws('Thread Locks Owned')
#     finally:
#         setIRLMTimeout(user, password, sys, ssid)
#
# #Special threads
#
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_STP():
#     stpWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m'}}".format(user, password, sys, ssid))
#     time.sleep(10)
#     navigate_to_node('Thread Activity')
#     check_ws('Thread Activity by Plan')
#     if server_version != '530':
#         navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Thread Status', 'IN-STOR-PROC')
#     else:
#         #thread status in 530 is not in-stor-proc
#         navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'SPSS_.*')
#     check_ws('Thread Detail')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_Triggers():
#     triggerWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m'}}".format(user, password, sys, ssid))
#     navigate_to_node('Thread Activity')
#     check_ws('Thread Activity by Plan')
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Thread Status', 'IN-TRIGGER')
#     check_ws('Thread Detail')
#
# @pytest.mark.tepsingle
# def test_Thread_Activity_UDF():
#     udfWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'3m'}}".format(user, password, sys, ssid))
#     navigate_to_node('Thread Activity')
#     check_ws('Thread Activity by Plan')
#
#     dict_new = {'Collection ID (Unicode)': '^THIS_IS_A_LONG_NAMED_COLLECTION_FOR_TDKUFUN$'}
#     dict_old = update_regexp('Thread Detail', 'Thread ID', dict_new)
#
#     navigate_to_subnode_on_condition('Thread Activity by Plan','Top Ten In-DB2 CP CPU Time Threads','Thread Detail', 'Package DBRM (Unicode)', 'TDKUFUN')
#     check_ws('Thread Detail')
#     update_regexp('Thread Detail', 'Thread ID', dict_old)
#
#
# #ZPARM single
#
#
# @pytest.mark.tepsingle
# def test_ZPARM_Thread():
#     navigate_to_node('Installation Parameters')
#     check_ws('DSNZPARM Thread Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Trace():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(1)
#     check_ws('DSNZPARM Trace Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Logging():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(2)
#     check_ws('DSNZPARM Logging Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Archiving():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(3)
#     check_ws('DSNZPARM Archiving Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Auth():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(4)
#     check_ws('DSNZPARM Authorization/ RLF/ DDF Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_IRLM():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(5)
#     check_ws('DSNZPARM IRLM Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Storage():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(6)
#     check_ws('DSNZPARM Storage and Size Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Dataset():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(7)
#     check_ws('DSNZPARM Data Set and Database Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_DDCS():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(8)
#     check_ws('DSNZPARM Data Definition Control Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Data_Sharing():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(9)
#     check_ws('DSNZPARM Data Sharing Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_STP():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(10)
#     check_ws('DSNZPARM Stored Procedure Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Utility():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(11)
#     check_ws('DSNZPARM Utility Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Application():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(12)
#     check_ws('DSNZPARM Application Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Data():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(13)
#     check_ws('DSNZPARM Data Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Performance():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(14)
#     check_ws('DSNZPARM Performance and Optimization Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Bufferpool():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(15)
#     check_ws('DSNZPARM Buffer Pool Parameters')
#
# @pytest.mark.tepsingle
# def test_ZPARM_html_Others():
#     navigate_to_node('Installation Parameters')
#     time.sleep(10)
#     sendTabsAndEnter(16)
#     check_ws('DSNZPARM Other System Parameters')
#
#
# #System HTML Links
#
#
# @pytest.mark.tepsingle
# def test_system_html_DB2C():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(1)
#     check_ws_info('DB2 Connect Server')
#
# @pytest.mark.tepsingle
# def test_system_html_EDM():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(2)
#     check_ws_info('System Resource Manager (EDM)')
#
# @pytest.mark.tepsingle
# def test_system_html_Log():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(3)
#     check_ws_info('System Resource Manager (Log)')
#
# @pytest.mark.tepsingle
# def test_system_html_Storage_Consumption():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(4)
#     check_ws_info('Storage Consumption')
#
# @pytest.mark.tepsingle
# def test_system_html_Subsystem_Management():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(5)
#     check_ws_info('System Resource Manager (Subsystem)')
#
# @pytest.mark.tepsingle
# def test_system_html_System_Status():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(6)
#     check_ws_info('System Status')
#
# @pytest.mark.tepsingle
# def test_system_html_SQL1():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(7)
#     args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','jcl':'runDDLCommandsForStats.jcl','duration':'1m'}}".format(user, password, sys, ssid)
#     run_workload('WorkloadRun.xml', 'RunJob', args_str)
#     args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'4m', 'wklOptions':'STATEMENTS=50'}}".format(user, password, sys, ssid, wkl_machine)
#     run_workload('RunDB2WKL.xml', 'DataManipulationLanguageWorkload', args_str)
#     time.sleep(5)
#     refresh()
#     check_ws('SQL Counts 1')
#
#
# @pytest.mark.tepsingle
# def test_system_html_SQL2():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(8)
#
#     args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'4m', 'wklOptions':'F=simpletime;S=2'}}".format(user, password, sys, ssid, wkl_machine)
#     run_workload('RunDB2WKL.xml', 'STPWorkload', args_str)
#
#     args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'4m', 'wklOptions':'SQL=select count(*) from sysibm.syscolumns;D=1;seconds=2'}}".format(user, password, sys, ssid, wkl_machine)
#     run_workload('RunDB2WKL.xml', 'UDFWithSQLWorkload', args_str)
#
#     args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','duration':'4m'}}".format(user, password, sys, ssid)
#     run_workload('WorkloadRun.xml', 'RunTrigger', args_str)
#
#     args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'4m', 'wklOptions':'seconds=240'}}".format(user, password, sys, ssid, wkl_machine)
#     run_workload('RunDB2WKL.xml', 'DirectRowAccessWorkload', args_str)
#
#     try:
#         args_str = "{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','jcl':'singleSelectLongDSNTEP2DegreeANY.jcl','duration':'1m'}}".format(user, password, sys, ssid)
#         job_id = run_workload('WorkloadRun.xml', 'RunJob', args_str)
#
#         time.sleep(5)
#         refresh()
#
#         check_ws('SQL Counts 2')
#     finally:
#         args = "{{'user':'{}','password':'{}','hostname':'{}','command':'{}'}}".format(user, password, sys, f'c {job_id}')
#         runSDSFCommand(args)
#
#
# @pytest.mark.tepsingle
# def test_system_html_SQL3():
#     navigate_to_node('Buffer Pool Management')
#     time.sleep(10)
#     sendTabsAndEnter(9)
#     check_ws('SQL Counts 3')
#
# @pytest.mark.tepsingle
# def test_system_html_BPM():
#     navigate_to_node('DB2 Connect Server')
#     time.sleep(10)
#     sendTabsAndEnter(1)
#     check_ws_info('Buffer Pool Management')
#
#
# #better to run in the end
#
# def switch_db2_messages(switch = True):
#     sw = 'N'
#     if switch:
#         sw = 'Y'
#     command = 'F {},F PESERVER,F {},DB2MSGMON={}'.format(collector, ssid, sw)
#     args = "{{'user':'{}','password':'{}','hostname':'{}','command':'{}'}}".format(user, password, sys, command)
#     runSDSFCommand(args)
#
# @pytest.mark.tepsingle
# def test_DB2_Messages():
#     #needs OMPEOPTS(MGSUBSYS=ACTIVE) and f OMPQ01S,F PESERVER,F qca3,DB2MSGMON=Y
#     switch_db2_messages(True)
#
#     lockWorkload("{{'user':'{}','password':'{}', 'hostname':'{}','ssids':'{}','machine':'{}','duration':'5m', 'wklOptions':'MODE=DL;LOCKTIME=60'}}".format(user, password, sys, ssid, wkl_machine))
#     time.sleep(60)
#
#     try:
#         navigate_to_node('DB2 Messages')
#         check_ws('DB2 Messages')
#         navigate_to_subnode('DB2 Messages','Critical DB2 Messages','Critical DB2 Messages by Message ID')
#         check_ws('Critical DB2 Messages by Message ID')
#         navigate_to_subnode('Critical DB2 Messages by Message ID','Critical DB2 Messages by Message ID','DB2 Messages')
#         navigate_to_subnode('DB2 Messages','Last 10 DB2 Messages','DB2 Messages by Time Interval')
#         check_ws('DB2 Messages by Time Interval')
#         navigate_to_subnode('DB2 Messages by Time Interval','DB2 Messages by Time Interval','DB2 Messages by Message ID')
#         check_ws('DB2 Messsages by Message ID')  #here typo in wks name - triple s
#         navigate_to_subnode('DB2 Messsages by Message ID','DB2 Messages by Message ID','DB2 Messages')
#     finally:
#         switch_db2_messages(False)
#         setIRLMTimeout(user, password, sys, ssid)
