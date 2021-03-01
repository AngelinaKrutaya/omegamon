# import pexpect
import os
import shutil
import re
from pathlib import Path
from pexpect import popen_spawn
import pytest
from libs.creds import *
from libs.ivtenv import rtes

rte = os.environ.get('rte', 'ite4')
teps = rtes[rte]['teps'].upper()

# Win2012 server has small 'c' in c:\ prompt, so we ignore case
command_prompt = r'(?i)C:\\'
regex_prefix = 'regex:'


def _open_cmd_logon():
    child = popen_spawn.PopenSpawn('cmd')
    child.sendline(f"tacmd login -s {rtes[rte]['hostname']}:{rtes[rte]['tems_http']} -u {username} -p {password}")
    child.expect(f'KUIC00007I: User {username} logged into server')
    child.expect(command_prompt)
    return child


@pytest.fixture(scope='module')
def tacmd():
    return _open_cmd_logon()


@pytest.fixture(scope='function')
def tacmd_single():
    return _open_cmd_logon()


@pytest.mark.parametrize('command, expected', [
    ('listappinstallrecs', rf'{regex_prefix}{rte.upper()}:CMS\s+DP'),

    ('listcalendarentries', 'Name: Weekend'),

    ('creategroup -g newGroup -t situation', 'KUICGR012I: The group newGroup was successfully created'),
    ('listgroups', 'Name: newGroup'),
    ('viewgroup -g newGroup  -t situation', 'Name         : newGroup'),
    ('addgroupmember -g newGroup -m NT_Disk_Space_Low -t situation',
     'The member NT_Disk_Space_Low was successfully added to group newGroup'),
    ('viewgroupmember -g newGroup -t situation -m NT_Disk_Space_Low', 'Name            : NT_Disk_Space_Low'),
    ('editgroup -g newGroup -t SITUATION -d test2 -f', 'The group newGroup was updated successfully'),
    ('viewgroup -g newGroup  -t situation', 'Description  : test2'),
    ('deletegroup -g newGroup -t situation -f', 'The group newGroup was successfully deleted from the server'),

    ('listsdainstalloptions', 'The default SDA installation setting is: [ON]'),
    ('editSdaInstallOptions -t DEFAULT -i ON', 'The default SDA installation setting is: [ON]'),

    ('listsdastatus', rf'{regex_prefix}{rte.upper()}:CMS \s+ON'),

    ('listsit', 'Sysplex_XCFSystems_Status_Warn'),

    ('listsystems', f'{teps}:TEPS'),

    ('listsystemlist', '*MVS_DB2'),

    ('listaction', 'MQ Start Channel'),

    (f'listtrace -m {rte.upper()}:CMS -p KBB_RAS1', f'The current value of KBB_RAS1 at {rte.upper()}:CMS is'),

    ('createSit -s MySit -b KD5_ETIM_Warning -p runonstart=no', 'The situation MySit was created on the server'),
    ('viewsit -s MySit', 'Name                   : MySit'),
    ('editSit -s MySit -p desc=test -f', 'The situation MySit was updated on server'),
    ('viewsit -s MySit', 'Description            : test'),
    ('deletesit -s MySit -f', 'The situation MySit was deleted from the server'),

    ('createsystemlist -l testList1 -b "*MVS_DB2"', 'The system list testList1 was created on the server'),
    ('editsystemlist -l testList1 -d ICD4:RSD4:DB2 -f', 'The system list testList1 has been updated on the server'),
    ('viewsystemlist -l testList1', 'Name                    : testList1'),
    ('listsystemlist', 'testList1                       DB2 Subsystems'),
    ('deletesystemlist -l testList1 -f', 'The system list testList1 was deleted from the server'),

    ('createAction -n "newAction" -t DP -p cmd="test"', 'The action newAction was successfully created on the server'),
    ('editaction -n "newAction" -p cmd="test2" -f', 'The action newAction was updated successfully'),
    ('viewaction -n "newAction"', 'Command    : test2'),
    ('deleteAction -n "newAction" -f', 'The action newAction was deleted from the server'),

    (f'viewagent -m {rte.upper()}:CMS',
     'The viewAgent command did not complete because this command is not supported by a z/OS Hub'),

    ('addCalendarEntry -n Clean_Temp -d "Clean Temporary directory on weekend" -c "30 21 * * SUN"',
     'The calendar entry Clean_Temp was successfully added on the server'),
    ('editcalendarentry -n Clean_Temp -d test -f',
     'The calendar entry Clean_Temp was successfully updated on the server'),
    ('viewcalendarentry -n Clean_Temp', 'Description: test'),
    ('deletecalendarentry -n Clean_Temp -f', 'The calendar entry name Clean_Temp was deleted from the server'),

    ('createEventDest -i 123 -p host1=bigTECserver:4567 desc=test1 name=myTEC -f',
     'The event destination server definition myTEC with server ID 123 was successfully created on the server'),
    ('editeventdest -i 123 -p desc=test2 -f',
     'The event destination server definition myTEC with server ID 123 was successfully modified on the server'),
    ('vieweventdest -i 123', 'Description: test2'),
    ('listeventdest', rf'{regex_prefix}123\s+myTEC\s+TEC'),
    ('deleteeventdest -i 123 -f',
     'The event destination server definition myTEC with server ID 123 was successfully deleted from the server'),

    (f'viewnode -n Primary:{teps}:NT', f'{teps}:TEPS       CQ'),

    ('viewsystemlist -l "*ALL_CMS"', 'Name                    : *ALL_CMS'),

    ('executecommand -m "" -c "" -v -r -o',
     'The executecommand command did not complete because an incorrect managed system'),

])
def test_tacmd(tacmd, command, expected):
    tacmd.sendline('tacmd ' + command)
    tacmd.expect(command_prompt, timeout=180)
    if expected.startswith(regex_prefix):
        assert re.search(expected[len(regex_prefix):], tacmd.before.decode('utf-8'))
    else:
        assert expected in tacmd.before.decode('utf-8')


@pytest.mark.parametrize('command, expected', [
    ('bulkexportsit -p %TMP% -f', 'All of the situations were successfully exported from the managed server'),
])
def test_bulkexport(tacmd_single, command, expected):
    temp_env = os.environ.get('TMP')
    temp_folder = Path(temp_env + '/Bulk')
    shutil.rmtree(temp_folder, ignore_errors=True)

    tacmd_single.sendline('tacmd ' + command)
    tacmd_single.expect(command_prompt, timeout=180)
    assert expected in tacmd_single.before.decode('utf-8')
    sit_filename = Path(temp_env + '/Bulk' + '/SITUATION/S3/KS3_VTS_Virt_MtPend_Mx_Warning.xml')
    assert sit_filename.exists()

# def test_bulkimport(tacmd_single, command, expected):
# TODO
