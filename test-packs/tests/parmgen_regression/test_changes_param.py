import os
import pytest
import re

from taf import logging

from libs.parmgen import Parmgen
from libs.creds import *
from libs.ivtenv import rtes
import libs.utils as util

hostname = Parmgen.exec_host
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

rte = os.environ.get('rte')
is_new = os.environ.get('is_new')
logger = logging.getLogger(__name__)
hlq = rtes[rte]['rte_hlq']
config_variable = ''

# define config for rte with vars
if rtes[rte].get('vars', False):
    config_variable = f"{hlq[0:hlq.rfind('.')]}.PARMGEN.JCL({rte})"

# create new rte
if is_new == 'true':
    rte1 = Parmgen(username, password, rtes['ite1']['rte_hlq'][0:rtes['ite1']['rte_hlq'].rfind('.')], 'ite1')
    try:
        rte1.logon()
        rte1.delete_another_rte(rte)
    except TypeError:
        print(f'{rte} not found in rtes list')
    finally:
        rte1.logoff()

    rte1 = Parmgen(username, password, hlq[0:hlq.rfind('.')], rte, is_new=True, rte_model=rtes[rte]['rte_model'],
                   rte_products=rtes[rte]['rte_products'], rte_type=rtes[rte]['type'])

    try:
        rte1.logon()
        rte1.step_1_set_up()
    finally:
        rte1.logoff()
else:
    rte1 = Parmgen(username, password, hlq[0:hlq.rfind('.')], rte, rte_model=rtes[rte]['rte_model'])

config_changes = {
    'itp1': {
        'parm-106':
            {
                'parameters': {
                    'RTE_USS_MKDIR_MODE': '775'
                },
                'result': {'RKANDATV(KQIMKDIR)': r'MODE\(7,7,5\)', 'RKANDATV(KQIUSS)': r'chmod\s+775'}
            },
        'parm-108':
            {
                'parameters': {
                    'KYN_XAI01_SUBAGENT_JAVAHOME': "/rsusr/java/IBM/J7.1",
                    'KYN_XAI01_SUBAGENT_PRODHOME': "/proj/omivt/itd/ITP1/itcam71"
                },
                'result': {'WKANSAMU(KYNUSSJB)': r'then\s+'}
            },
        'parm-139':
            {
                'parameters': {
                    'KM2_CLASSIC_PASSPHRASE': 'NO',
                    'KM2_CLASSIC_SECCLASS': 'OMCANDLE',
                    'KM2_CLASSIC_SAFAPPL': 'CANDLE',
                },
                'result': {'RKANPARU(KOBVTAM)': [r'PASSPHRASE=NO\nSECCLASS=OMCANDLE\nSAFAPPL=CANDLE\nPRTCT=\nPSWD='],
                           f'RKANSAMU({rte}M2RC)': [r'//\s+MEMBER=KOBVTAM,\n//[*]\s+PRTCT=,\n//[*]\s+PSWD=,',
                                                    r'//\s+\'MEMBER=&MEMBER\',\n//[*]\s+\'PSWD=&PSWD,PRTCT=&PRTCT']
                           }
            },
        'parm-339':
            {
                'parameters': {
                    'KOB_MT_ENABLE': 'Y'
                },
                'result': {
                    f'RKANSAMU({rte}TOM)': r'//\s+\'MULTI=Y\','
                }
            },
        'parm-173-1':
            {
                'parameters': {
                    'KN3_SNA_VTAM_APPS': 'N',
                    'KN3_TCP_ZERT': 'Y',
                },
                'result': {
                    'RKANCMDU(KN3AGOPS)': r'[*]\${4}\s+KN3FCCMD\s+START\s+VAPP\n\${4}\s+KN3FCCMD\s+STOP\s+VAPP',
                    'RKANCMDU(KN3AGOPT) ': [r'\${4}\s+KN3FCCMD\s+START\s+ZERT\s+\+\n\s+TCPNAME\(\$+\)',
                                            r'\${4}\s+KN3FCCMD\s+STOP\s+ZERT'],
                }
            },
        'parm-173-2': {
            'parameters': {
                'KN3_TCPX01_OVRD_GLOBAL_FLAG': 'Y',
                'KN3_TCPX01_OVRD_ZERT': 'Y',
                'KN3_TCPX02_OVRD_GLOBAL_FLAG': 'Y',
                'KN3_TCPX02_OVRD_ZERT': 'N',
            },
            'result': {
                'RKANCMDU(KN3A#01)': [r'\${4}\s+KN3FCCMD\s+START\s+GLBS\s+\+\n\s+TCPNAME\(\$+\)',
                                      r'[*]\${4}\s+KN3FCCMD\s+STOP\s+GLBS',
                                      r'\${4}\s+KN3FCCMD\s+START\s+ZERT\s+\+\n\s+TCPNAME\(\$+\)',
                                      r'[*]\${4}\s+KN3FCCMD\s+STOP\s+ZERT'],
                'RKANCMDU(KN3A#02)': [r'\${4}\s+KN3FCCMD\s+START\s+GLBS\s+\+\n\s+TCPNAME\(\$+\)',
                                      r'[*]\${4}\s+KN3FCCMD\s+STOP\s+GLBS',
                                      r'[*]\${4}\s+KN3FCCMD\s+START\s+ZERT\s+\+\n\s+TCPNAME\(\$+\)',
                                      r'\${4}\s+KN3FCCMD\s+STOP\s+ZERT'],
            }
        },
        'parm-185':
            {
                'parameters': {
                    'KDS_TEMS_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KC5_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KD5_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KGW_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KI5_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KJJ_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KMQ_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KN3_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KQI_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                    'KYN_AGT_TCP_KDEB_INTERFACELIST': '"|192.168.0.1"',
                },
                'result': {
                    'RKANPARU(KCICFG00)': r'KDS_TEMS_TCP_KDEB_INTERFACELIST\s+|192.168.0.1'
                }
            },
        'parm-794':
            {
                'parameters': {
                    'RTE_VALIDATION_LEVEL': 'I',
                    'KC5_AGT_TCP_KDEB_INTERFACELIST': '""'
                },
                'result': {
                    'WCONFIG($VALRPT)': [r'Validation\sReturn\sCode\s[=]\s8',
                                         r' E\sKDEB[_]INTERFACELIST\svalues']
                }
            },
        'parm-1064': {
            'parameters': {
                'KD2_DB01_DB2_SSID': 'P001',
                'KD2_DB01_DB2_DESCRIPTION': '"P001 DB2 Subsystem"',
                'KD2_PF01_PROFID': 'P001',
                'KD2_PF01_HIS_AD_ALPHA': '0.1',
                'KD2_PF01_HIS_AD_CPU_DSC_TOL': '10.0',
                'KD2_PF01_HIS_AD_CPU_TOL': '5.0',
                'KD2_PF01_HIS_AD_ELP_DSC_TOL': '10.0',
                'KD2_PF01_HIS_AD_ELP_TOL': '5.0',
                'KD2_PF01_HIS_AD_ENABLED': 'Y',
                'KD2_PF01_HIS_AD_GPG_DSC_TOL': '10.0',
                'KD2_PF01_HIS_AD_GPG_TOL': '5.0',
                'KD2_PF01_HIS_AD_MEMORY_SIZE': '2048',
                'KD2_PF01_HIS_AD_MIN_COUNT': '999',
                'KD2_PF01_HIS_AD_USE_AUTH': 'Y',
                'KD2_PF01_HIS_AD_USE_CONNECT': 'Y',
                'KD2_PF01_HIS_AD_USE_CONNNM': 'Y',
                'KD2_PF01_HIS_AD_USE_CORRID': 'Y',
                'KD2_PF01_HIS_AD_USE_PLAN': 'Y',
                'KD2_PF01_HIS_AD_USE_WSNAME': 'Y',
                'KD2_PF01_HIS_AD_USE_TRANSAC': 'Y',
                'KD2_PF01_HIS_AD_USE_ENDUSER': 'Y',
                'KD2_DB02_DB2_SSID': 'P002',
                'KD2_DB02_DB2_DESCRIPTION': '"P002 DB2 Subsystem"',
                'KD2_PF02_PROFID': 'P002',
                'KD2_PF02_ROW': '02',
                'KD2_PF02_HIS_AD_ALPHA': '0.1',
                'KD2_PF02_HIS_AD_CPU_DSC_TOL': '10.0',
                'KD2_PF02_HIS_AD_CPU_TOL': '5.0',
                'KD2_PF02_HIS_AD_ELP_DSC_TOL': '10.0',
                'KD2_PF02_HIS_AD_ELP_TOL': '5.0',
                'KD2_PF02_HIS_AD_ENABLED': 'N',
                'KD2_PF02_HIS_AD_GPG_DSC_TOL': '10.0',
                'KD2_PF02_HIS_AD_GPG_TOL': '5.0',
                'KD2_PF02_HIS_AD_MEMORY_SIZE': '2048',
                'KD2_PF02_HIS_AD_MIN_COUNT': '999',
                'KD2_PF02_HIS_AD_USE_AUTH': 'Y',
                'KD2_PF02_HIS_AD_USE_CONNECT': 'Y',
                'KD2_PF02_HIS_AD_USE_CONNNM': 'Y',
                'KD2_PF02_HIS_AD_USE_CORRID': 'Y',
                'KD2_PF02_HIS_AD_USE_PLAN': 'Y',
                'KD2_PF02_HIS_AD_USE_WSNAME': 'Y',
                'KD2_PF02_HIS_AD_USE_TRANSAC': 'Y',
                'KD2_PF02_HIS_AD_USE_ENDUSER': 'Y',
            },
            'clone_parameters': {
                'product_code': 'D2',
                'section': 'PF',
                'base_section_id': '01',
                'target_section_id': '02',
            },
            'result': {
                'WKD2PRF(COPTP001)':
                    r'[*]\s+For Anomaly Detection:\n'
                    r'ADALPHA\(0.1\)\n'
                    r'ADDCPUDTOLR\(10.0\)\n'
                    r'ADCPUTOLER\(5.0\)\n'
                    r'ADDELDTOLR\(10.0\)\n'
                    r'ADELTOLER\(5.0\)\n'
                    r'ADENABLED\(YES\)\n'
                    r'ADDGPDTOLR\(10.0\)\n'
                    r'ADGPTOLER\(5.0\)\n'
                    r'ADMEMSIZ\(2048\)\n'
                    r'ADMCOUNT\(999\)\n'
                    r'ADUAUTH\(Y\)\n'
                    r'ADUCONN\(Y\)\n'
                    r'ADUCONNNM\(Y\)\n'
                    r'ADUCORRID\(Y\)\n'
                    r'ADUPLAN\(Y\)\n'
                    r'ADUEUWN\(Y\)\n'
                    r'ADUEUTX\(Y\)\n'
                    r'ADUEUID\(Y\)',
                'WKD2PRF(COPTP002)':
                    r'[*]\s+For Anomaly Detection:\n[*]ADALPHA\(0.1\)\n'
                    r'[*]ADDCPUDTOLR\(10.0\)\n'
                    r'[*]ADCPUTOLER\(5.0\)\n'
                    r'[*]ADDELDTOLR\(10.0\)\n'
                    r'[*]ADELTOLER\(5.0\)\n'
                    r'[*]ADENABLED\(NO\)\n'
                    r'[*]ADDGPDTOLR\(10.0\)\n'
                    r'[*]ADGPTOLER\(5.0\)\n'
                    r'[*]ADMEMSIZ\(2048\)\n'
                    r'[*]ADMCOUNT\(999\)\n'
                    r'[*]ADUAUTH\(Y\)\n'
                    r'[*]ADUCONN\(Y\)\n'
                    r'[*]ADUCONNNM\(Y\)\n'
                    r'[*]ADUCORRID\(Y\)\n'
                    r'[*]ADUPLAN\(Y\)\n'
                    r'[*]ADUEUWN\(Y\)\n'
                    r'[*]ADUEUTX\(Y\)\n'
                    r'[*]ADUEUID\(Y\)'
            }
        },
        'parm-1239': {
            'parameters': {
                'KDS_SAFAPPL': '"DEFAULT APPL(CANDLE)"',
            },
            'result': {
                'WKANPARU(KDSINNAM)': r'DEFAULT\s+APPL\(CANDLE\)\s+[-]',
            }
        },
        'parm-1351': {
            'parameters': {
                'KC2_CC01_ROW': '01',
                'KC2_CC01_CLASSIC_XMIT ': '00',
                'KC2_CC01_CLASSIC_STC': 'ITP1OC0',
                'KC2_CC01_CUA_STC': 'ITP1C20',
                'KC2_CC01_CLASSIC_VTAM_APPL_LOGON': 'ITP1OC0',
                'KC2_CC01_CUA_VTAM_NODE': 'ITP1C20N',
                'KC2_CC01_CUA_VTAM_APPL_LOGON': 'ITP1C20',
                'KC2_CC01_CUA_VTAM_APPL_OPERATOR': 'ITP1C20O ',
                'KC2_CC01_CUA_VTAM_VTPOOL_PREFIX': 'ITP1C0 ',
                'KC2_CC01_CUA_CICS_REGION': "*",
                'KC2_CC02_ROW': '02',
                'KC2_CC02_CLASSIC_XMIT ': '01',
                'KC2_CC02_CLASSIC_STC': 'ITP1OC1',
                'KC2_CC02_CUA_STC': 'ITP1C21',
                'KC2_CC02_CLASSIC_VTAM_APPL_LOGON': 'ITP1OC1',
                'KC2_CC02_CUA_VTAM_NODE': 'ITP1C21N',
                'KC2_CC02_CUA_VTAM_APPL_LOGON': 'ITP1C21',
                'KC2_CC02_CUA_VTAM_APPL_OPERATOR': 'ITP1C21O ',
                'KC2_CC02_CUA_VTAM_VTPOOL_PREFIX': 'ITP1C1',
                'KC2_CC02_CUA_CICS_REGION': "*",
            },
            'clone_parameters': {
                'product_code': 'C2',
                'section': 'CC',
                'base_section_id': '01',
                'target_section_id': '02',
            },
            'result': {
                'WKANSAMU(KCIJPSYS)': [
                    r'\s+COPY\s+INDD[=]RKANSAMU[,]OUTDD[=]PROCLIB\n\s+SELECT\s+MEMBER[=]\(\(ITP1OC0[,][,]R\)\)',
                    r'\s+COPY\s+INDD[=]RKANSAMU[,]OUTDD[=]PROCLIB\n\s+SELECT\s+MEMBER[=]\(\(ITP1OC1[,][,]R\)\)'],
            }
        }
    },
    'itp4':
        {
            'parm-248': {
                'parameters': {
                    'KS3_NODEJS_HOME': '/rsusr/cnj/IBM/node-v6.14.4-os390-s390x',
                    'KS3_AS_LISTENER_ADDR': '""',
                    'KDS_TEMS_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KC5_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KD5_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KGW_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KI5_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KJJ_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KMQ_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KN3_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KQI_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                    'KYN_AGT_TCP_KDEB_INTERFACELIST': '&KDEB_INTERFACELIST.',
                },
                'variables': {
                    'RTE_USS_RTEDIR': '/proj/omivt/itd/',
                    'OMEGSAF': '"OMEGDEMO"'
                },
                'result': {
                    'RKANSAMU(ITP4S3AP)': '/proj/omivt/itd/'
                }
            }
        },
    'itp5': {
        'parm-1166': {
            'parameters': {
                'KN3_TCP_ZERT': 'Y',
                'KN3_SNA_VTAM_APPS': 'Y',
            },
            'result': {
                'RKANCMDU(KN3AGOPS)': r'\${4}\s+KN3FCCMD\s+START\s+VAPP\n[*]\${4}\s+KN3FCCMD\s+STOP\s+VAPP',
                'RKANCMDU(KN3AGOPT)': r'\$\$\$\$\s+KN3FCCMD\s+START\s+ZERT'
            }
        }
    },
    'itcc': {
        'parm-1278': {
            'parameters': {
                'KAG_X_KDE_TRANSPORT_GBL_OPTIONS': '""',
                'KAG_X_KDE_TRANSPORT_HTTP_OPTIONS': '""',
            },
            'result': {
                'WKANPARU(KM2ENV)': r'KDE[_]TRANSPORT[=]\\\n\s+\\\n\s+\\\n\s+IP[.]PIPE',
                'WKANCMDU(KM2DFVSM)': r'VSM\s+DEF\s+[$]DEFAULT\s+ITCCM201\s+[-]\s+'
            }
        }
    },
}


def setup_module():
    config_parameters = {}
    variables = {}
    for value in config_changes[rte].values():
        try:
            parameter = value['clone_parameters']
            rte1.include_parameters(parameter['product_code'], parameter['section'], parameter['base_section_id'],
                                    parameter['target_section_id'])
        except KeyError:
            pass
        config_parameters.update(value['parameters'])
        try:
            if rtes[rte]['rte_model'] in rte1.VARS_MODELS:
                variables.update(value['variables'])
        except KeyError:
            logger.info('Rte model without variables')
    util.upload_member_in_ds(hostname, username, password, ['ITM.ITE.TKANWENU(KN3VAAO)', ])
    rte1.save_config(dataset=config_variable)
    try:
        rte1.logon()
        rte1.step_1_set_up()
        rte1.change_parameters(params=config_parameters, variables=variables, dataset=config_variable)
        rte1.full_update(change_params=True)
    finally:
        rte1.restore_config(dataset=config_variable)
        rte1.logoff()


def teardown_module():
    rte1.restore_config(dataset=config_variable)


@pytest.mark.parametrize("results", [value['result'] for value in config_changes[rte].values()])
def test_check_parameters(results, zosmf):
    assert Parmgen.verify_values_in_datasets(results, zosmf, rte)
