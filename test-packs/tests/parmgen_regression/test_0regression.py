import os
import pytest
import re
from taf.zos.jes import JESAdapter
from taf.zos.py3270 import ISPF
from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys
from libs.rte import RteType

import logging

from libs.parmgen import Parmgen, ParmException
from libs.creds import *
from libs.ivtenv import rtes

hostname = Parmgen.exec_host
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)
rte = 'itp1'
hlq = rtes[rte]['rte_hlq']

logger = logging.getLogger(__name__)

products = \
    '''
IBM Advanced Archive for DFSMShsm                                 V1.1.0
IBM Cloud Tape Connector for z/OS                                 V1.1.0
IBM DB2 Buffer Pool Analyzer                                      V5.3.0
IBM OMEGAMON for z/OS                                             V5.5.0
IBM OMEGAMON for CICS on z/OS                                     V5.5.0
IBM OMEGAMON for IMS on z/OS                                      V5.5.0
IBM OMEGAMON for JVM on z/OS                                      V5.4.0
IBM OMEGAMON for Messaging on z/OS                                V7.5.0
IBM OMEGAMON for Networks on z/OS                                 V5.5.0
IBM OMEGAMON for Storage on z/OS                                  V5.4.0
IBM OMEGAMON for Storage on z/OS                                  V5.5.0
IBM OMEGAMON Dashboard Edition on z/OS                            V5.5.0
IBM Tivoli Advanced Allocation Management for z/OS                V3.2.0
IBM Tivoli Advanced Allocation Management for z/OS                V3.3.0
IBM Tivoli Advanced Audit for DFSMShsm                            V2.5.0
IBM Tivoli Advanced Audit for DFSMShsm                            V2.6.0
IBM Tivoli Advanced Backup and Recovery for z/OS                  V2.4.0
IBM Tivoli Advanced Catalog Management for z/OS                   V2.5.0
IBM Tivoli Advanced Catalog Management for z/OS                   V2.6.0
IBM Tivoli Advanced Reporting and Management for DFSMShsm         V2.5.0
IBM Tivoli Advanced Reporting and Management for DFSMShsm         V2.6.0
IBM Tivoli Advanced VSAM Manager for z/OS                         V2.6.0
IBM Tivoli Automated Tape Allocation Manager for z/OS             V3.3.0
IBM Tivoli Decision Support for z/OS                              V1.8.1
IBM Tivoli Discovery Library Adapter for z/OS                     V3.1.0
IBM Tivoli Management Services on z/OS                            V6.2.3
IBM Tivoli Management Services on z/OS                            V6.3.0
IBM Tivoli OMEGAMON Dashboard Edition on z/OS                     V5.3.0
IBM Tivoli OMEGAMON XE for CICS on z/OS                           V5.3.0
IBM Tivoli OMEGAMON XE for DB2 Performance Expert on z/OS         V5.3.0
IBM Tivoli OMEGAMON XE for DB2 Performance Expert on z/OS         V5.4.0
IBM Tivoli OMEGAMON XE for DB2 Performance Monitor on z/OS        V5.3.0
IBM Tivoli OMEGAMON XE for DB2 Performance Monitor on z/OS        V5.4.0
IBM Tivoli OMEGAMON XE for IMS on z/OS                            V5.3.0
IBM Tivoli OMEGAMON XE for Mainframe Networks                     V5.3.0
IBM Tivoli OMEGAMON XE for Messaging for z/OS                     V7.3.0
IBM Tivoli OMEGAMON XE on z/OS                                    V5.3.0
IBM Tivoli Tape Optimizer for z/OS                                V2.2.0
IBM Z OMEGAMON for JVM                                            V5.5.0
IBM Z OMEGAMON Integration Monitor                                V5.6.0
IBM Z OMEGAMON Monitor for z/OS                                   V5.6.0
IBM Z OMEGAMON Network Monitor                                    V5.6.0
IBM Z OMEGAMON Runtime Edition for JVM                            V5.5.0
ITCAM for Application Diagnostics on z/OS                         V7.1.0
'''

db2_anomaly_detection = [
    'KD2_PF01_HIS_AD_ALPHA',
    'KD2_PF01_HIS_AD_CPU_DSC_TOL',
    'KD2_PF01_HIS_AD_CPU_TOL',
    'KD2_PF01_HIS_AD_ELP_DSC_TOL',
    'KD2_PF01_HIS_AD_ELP_TOL',
    'KD2_PF01_HIS_AD_ENABLED',
    'KD2_PF01_HIS_AD_GPG_DSC_TOL',
    'KD2_PF01_HIS_AD_GPG_TOL',
    'KD2_PF01_HIS_AD_MEMORY_SIZE',
    'KD2_PF01_HIS_AD_MIN_COUNT',
    'KD2_PF01_HIS_AD_USE_AUTH',
    'KD2_PF01_HIS_AD_USE_CONNECT',
    'KD2_PF01_HIS_AD_USE_CONNNM',
    'KD2_PF01_HIS_AD_USE_CORRID',
    'KD2_PF01_HIS_AD_USE_PLAN',
    'KD2_PF01_HIS_AD_USE_WSNAME',
    'KD2_PF01_HIS_AD_USE_TRANSAC',
    'KD2_PF01_HIS_AD_USE_ENDUSER'
]


@pytest.fixture(scope='module')
def jes_adapter():
    return JESAdapter(hostname, username, password)


def verify_text_in_member(hlq_rte, rte, zosmf, member, text_to_find, from_beginning=True, text_exist=True):
    """

    :param rte: rte
    :param zosmf: zosmf instance
    :param member: one member or list of members
    :param text_to_find: list of text to find
    :param from_beginning: from beginning of the string (default) or not
    :return:
    """
    if isinstance(member, str):
        mbs = [member]
    else:
        mbs = member
    for member in mbs:
        member = member.replace('{rte}', rte)
        member_text = zosmf.read_ds(f"{hlq_rte}.{member}")
        if from_beginning:
            pref = '^'
        else:
            pref = ''
        for text in text_to_find:
            if text_exist:
                assert re.search(pref + re.escape(text), member_text, re.MULTILINE), f'no {text} in {member}'
            else:
                assert not re.search(pref + re.escape(text), member_text, re.MULTILINE), f'{text} in {member}'


def verify_members(rte, zosmf, member, member_exist=True):
    """

    :param rte: rte
    :param zosmf: zosmf instance
    :param member: one member or list of members
    :return:
    """
    if isinstance(member, str):
        mbs = [member]
    else:
        mbs = member
    for member in mbs:
        member = member.replace('{rte}', rte)
        try:
            member_text = zosmf.read_ds(f"{rtes[rte]['rte_hlq']}.{member}")
            assert member_text and member_exist, f'{member} exist in {rtes[rte]["rte_hlq"]}.{member}'
        except:
            if rtes[rte]['type'] == RteType.SHARED:
                try:
                    member_text = zosmf.read_ds(f"{rtes[rte]['shared_ds']}.{member}")
                    assert member_text and member_exist, f'{member} exist in {rtes[rte]["rte_hlq"]}.{member}'
                except:
                    assert not member_exist, f'{member} not exist in {rtes[rte]["rte_hlq"]}.{member}'
            else:
                assert not member_exist, f'{member} not exist in {rtes[rte]["rte_hlq"]}.{member}'


@pytest.mark.parametrize("rte", ['itp1', 'itp2', 'itp3'])
@pytest.mark.parametrize("member, text_to_find", [
    ('RKANSAMU({rte}TOM)', ["//          'MULTI=N',"]),
    ('RKANPARU(KOBENV)', ["*KOB_SAF_FAILURE=CONSOLE",
                          "*KOB_SAF_LOGON_TRACE=YES",
                          ]),
    ('WCONFIG({rte})', ["KOB_MT_ENABLE",
                        ]),
    ('RKANSAMU({rte}JT)', ["//JTCOLL  PROC RGN=0M,TIM=1440,",
                           "//JTCOLL  EXEC PGM=KJTCOLL,REGION=&RGN,TIME=&TIM,",
                           ]),
    ('WCONFIG(KCIJPCFG)', ["  SELECT MEMBER=(KCIJPUP?,KCIJPPRF,KCIJPCCF)",
                           "  SELECT MEMBER=($JOBCARD,KCIJPVER,KCIJ$*)",
                           ]),
    ('RKD2PAR(RVTMNONE)', ["              PASSPHRASE=NO,                                           X",
                           "              SECCLASS=OMCANDLE,                                       X",
                           "              SAFAPPL=CANDLE",
                           ]),
    ('WCONFIG({rte})', db2_anomaly_detection),
],
                         ids=['parm-254',
                              'parm-310',
                              'parm-339-1',
                              'parm-658',
                              'parm-659',
                              'parm-139-1',
                              'parm-1064',
                              ]
                         )
def test_member_contains_something_from_beginning(rte, zosmf, member, text_to_find):
    verify_text_in_member(rtes[rte]['rte_hlq'], rte, zosmf, member, text_to_find)


@pytest.mark.parametrize("rte", ['itp1', 'itp2', 'itp3'])
@pytest.mark.parametrize("member, text_to_find", [
    ('TKCIINST(KCIDJG00)', ['CALDFLT  SCSQAUTH CSQ.V9R0M0.SCSQAUTH', 'CALDFLT  SCSQLOAD CSQ.V9R0M0.SCSQLOAD']),
],
                         ids=[
                             'parm-1002',
                         ]
                         )
def test_member_contains_something_for_other_datasets(rte, zosmf, member, text_to_find):
    verify_text_in_member(rtes[rte]['rte_hlq'][:-5], rte, zosmf, member, text_to_find)


@pytest.mark.parametrize("rte", ['itp1', 'itp2', 'itp3'])
@pytest.mark.parametrize("member, text_to_find", [
    ('RKANSAMU(KCIJPUPB)', ["%$IMBED_KMV_KCIJPUPB_NODE@% "]),
    ('RKANSAMU(KCIJPLOD)', ["KEPCOLL"]),
    (['WCONFIG({rte})'], ["ADETECT"]),
],
                         ids=[
                             'parm-912',
                             'parm-925',
                             'parm-1149',
                         ]
                         )
def test_member_not_contains_something_from_beginning(rte, zosmf, member, text_to_find):
    verify_text_in_member(rtes[rte]['rte_hlq'], rte, zosmf, member, text_to_find, text_exist=False)


@pytest.mark.parametrize("rte, member, text_to_find", [
    ('itp1', ['RKANSAMU(KOMCLIST)', 'RKANSAMU(KOMCLSTE)', 'RKANSAMU(KOMSPFU)'], ["'ITM.ITE.BASE.RKANPAR')"]),
    ('itp2', ['RKANSAMU(KOMCLIST)', 'RKANSAMU(KOMCLSTE)', 'RKANSAMU(KOMSPFU)'], ["'ITM.ITE.ITP2.RKANPAR')"]),
    ('itp1', ['RKANSAMU(KEPTSO)', 'RKANSAMU(KEDTSO)'], ["ITM.ITE.BASE.RKANPAR"]),
    ('itp2', ['RKANSAMU(KEPTSO)', 'RKANSAMU(KEDTSO)'], ["ITM.ITE.ITP2.RKANPAR"]),
    ('itp1', ['WCONFIG($VALRPT)'], ['GBL_DSN_SYS1_VTAMLIB']),
    ('itp1', ['WKANSAMU(ITP1OI0)', 'WKANSAMU(ITP1OI1)', 'WKANSAMU(ITP1DS)', 'WKANSAMU(ITP1D5)', 'WKANSAMU(ITP1JJ)',
              'WKANSAMU(ITP1JT)', 'WKANSAMU(ITP1I5)', 'WKANSAMU(ITP1N3)', 'WKANSAMU(ITP1MQ)', 'WKANSAMU(ITP1QI)',
              'WKANSAMU(ITP1YN)', 'WKANSAMU(ITP1C5)', 'WKANSAMU(ITP1OC0)', 'WKANSAMU(ITP1TOM)', 'WKANSAMU(ITP1GW)',
              'WKANSAMU(ITP1CN)'], ['MEMLIM=NOLIMIT']),
    ('itp1', ['WKANSAMU(ITP1DS)', 'WKANSAMU(ITP1D5)', 'WKANSAMU(ITP1JJ)', 'WKANSAMU(ITP1I5)', 'WKANSAMU(ITP1N3)',
              'WKANSAMU(ITP1MQ)', 'WKANSAMU(ITP1QI)', 'WKANSAMU(ITP1YN)', 'WKANSAMU(ITP1C5)', 'WKANSAMU(ITP1GW)'],
     ['REGION=&RGN,TIME=&TIM,MEMLIMIT=&MEMLIM\n//STEPLIB']),
],
                         ids=['parm-250-1',
                              'parm-250-2',
                              'parm-986-1',
                              'parm-986-2',
                              'parm-765',
                              'parm-1202',
                              'parm-1334',
                              ]
                         )
def test_member_contains_something(rte, zosmf, member, text_to_find):
    verify_text_in_member(rtes[rte]['rte_hlq'], rte, zosmf, member, text_to_find, from_beginning=False)


@pytest.mark.parametrize("rte, member, text_to_find", [
    pytest.param('itp1', ['RKD2PAR(COPTIBA3)', 'RKD2PAR(COPTIB1A)', 'RKD2PAR(COPTICA4)',
                          'RKD2PAR(COPTIC1A)', 'WKD2PAR(COPTIBA3)', 'WKD2PAR(COPTIB1A)', 'WKD2PAR(COPTICA4)',
                          'WKD2PAR(COPTIC1A)'], ["* For Anomaly Detection:"], marks=pytest.mark.skip()),
    pytest.param('itp2', ['RKD2PAR(COPTICA4)', 'WKD2PAR(COPTICA4)'], ["* For Anomaly Detection:"],
                 marks=pytest.mark.skip()),
],
                         ids=['parm-1149-1',
                              'parm-1149-2',
                              ]
                         )
def test_member_not_contains_something(rte, zosmf, member, text_to_find):
    verify_text_in_member(rtes[rte]['rte_hlq'], rte, zosmf, member, text_to_find, from_beginning=False,
                          text_exist=False)


@pytest.mark.parametrize("rte", ['itp1'])
def test_no_informational_message_during_start(rte):
    # parm-487
    em = Emulator(hostname, model=2, oversize=(24, 80))
    ispf = ISPF(em, username=username, password=password)
    tkancus = f"{rtes[rte]['hlq']}.TKANCUS".upper()
    try:
        d = ispf.em.display
        d('3.4').enter()
        d.find_by_label('Dsname Level . . .')('', keys.ERASEEOF)(tkancus).enter()
        d.find(f'        {tkancus}')('ex').enter()
        assert not d.find('For informational purposes only')
        assert d.find('KCIPQPGW')
    finally:
        ispf.logoff()


@pytest.mark.parametrize("rte", ['itp1'])
def test_all_products_available_in_jobgen(rte):
    # parm-487
    em = Emulator(hostname, model=2, oversize=(62, 160))
    ispf = ISPF(em, username=username, password=password)
    tkancus = f"{rtes[rte]['hlq']}.TKANCUS".upper()
    try:
        d = ispf.em.display
        d('3.4').enter()
        d.find_by_label('Dsname Level . . .')('', keys.ERASEEOF)(tkancus).enter()
        d.find(f'        {tkancus}')('ex').enter()
        assert d.find('KCIPQPGW')
        d('2').enter()
        if d.find('KCIP@TLV'):
            d(rtes[rte]['rte_hlq'][:-5]).enter()
        assert d.find('KCIPJG00')
        d(f'{username}.PARM.TEST.TMP').enter()
        # collect products from first screen
        all_products = str(d)
        # go to the next page
        d('', keys.PF8)
        all_products = all_products + str(d)
        assert all((prod in all_products for prod in products.split('\n')))
    finally:
        ispf.logoff()


@pytest.mark.parametrize("rte", ['itp1', 'itp2', 'itp3'])
@pytest.mark.parametrize("member", [('RKANSAMU(KOMSPFSC)', 'RKANSAMU(KOMSPFSI)', 'RKANSAMU(KOMSPFSX)'),
                                    ('RKANPARU(KS3STREP)'),
                                    ('RKANMOD(KEPCOLL)',)
                                    ],
                         ids=['parm-766',
                              'parm-1096',
                              'parm-925'
                              ]
                         )
def test_check_members_in_datasets(rte, zosmf, member):
    verify_members(rte, zosmf, member)


@pytest.mark.parametrize("parameter", db2_anomaly_detection)
def test_check_help_for_params(go_to_config, parameter):
    d = go_to_config
    d.find_by_label('==>')(f'f {parameter}').enter()
    d(key=keys.PF1)
    assert d.find('KCIPPGNH')
    d(key=keys.PF3)
