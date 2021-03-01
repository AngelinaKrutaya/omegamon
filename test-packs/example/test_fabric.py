from os import remove
from os.path import isfile

import pytest
from fabric import Connection, Config
from taf.af_support_tools import Config as TafConfig

testfilename = 'testfile'
remotepath = f'/tmp/{testfilename}'
test_text = 'testline'
conf = TafConfig('config.ini')
hostname = conf.get_option('linux_credentials', 'hostname')
username = conf.get_option('linux_credentials', 'username')
password = conf.get_option('linux_credentials', 'password')
cmd = 'whoami'


def test_1_fabric_run_non_sudo():
    c = Connection(host=hostname, user=username, connect_kwargs={'password': password})
    output = c.run(cmd, hide=True).stdout
    assert output.strip('\n') == username


def test_2_fabric_run_sudo():
    config = Config(overrides={'sudo': {'password': password}})
    c = Connection(host=hostname, user=username, connect_kwargs={'password': password}, config=config)
    output = c.sudo(cmd, hide=True).stdout
    assert output.strip('\n') == 'root'


def test_3_fabric_upload():
    remove(testfilename) if isfile(testfilename) else None
    localfile = open(testfilename, 'w')
    localfile.write(test_text)
    localfile.close()
    c = Connection(host=hostname, user=username, connect_kwargs={'password': password})
    c.put(testfilename, remotepath)
    output = c.run(f'cat {remotepath}').stdout
    assert output == test_text
    remove(testfilename)


def test_4_fabric_download():
    remove(testfilename) if isfile(testfilename) else None
    c = Connection(host=hostname, user=username, connect_kwargs={'password': password})
    c.get(remotepath)
    assert open(testfilename).readline() == 'testline'
    c.run(f'rm {remotepath}')
    remove(testfilename)
