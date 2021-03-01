import logging
import os

import pytest

from libs.parmgen import ParmException, Parmgen
from libs.creds import *
from libs.ivtenv import rtes

hostname = Parmgen.exec_host
username = os.environ.get('mf_user', username)
password = os.environ.get('mf_password', password)

logger = logging.getLogger(__name__)

rte = 'itp1'
hlq = rtes[rte]['rte_hlq']

config_changes = {
    # db2 anomaly detection
    # 'parm-570-5': {
    #    'parameters': {
    #       "KD2_ADETECT_ENABLED": "U",
    #       "KD2_ADETECT_MEMORY_SIZE": "500",
    #       "KD2_ADETECT_MIN_COUNT": "A",
    #       "KD2_ADETECT_ELAPSED_TOLERANCE": "B",
    #       "KD2_ADETECT_ELP_DSC_TOLERANCE": "C",
    #       "KD2_ADETECT_CPU_TOLERANCE": "D",
    #       "KD2_ADETECT_CPU_DSC_TOLERANCE": "E",
    #       "KD2_ADETECT_GETPAGE_TOLERANCE": "F",
    #       "KD2_ADETECT_GPG_DSC_TOLERANCE": "J",
    #       "KD2_ADETECT_ALPHA_SMOOTHING": "H",
    #       "KD2_ADETECT_USE_PLAN": "A",
    #       "KD2_ADETECT_USE_AUTH": "A",
    #       "KD2_ADETECT_USE_CORRID": "A",
    #       "KD2_ADETECT_USE_CONNNAME": "A",
    #       "KD2_ADETECT_USE_CONNECT": "A",
    #       "KD2_ADETECT_USE_WORKSTATION": "A",
    #       "KD2_ADETECT_USE_TRANSACTION": "A",
    #       "KD2_ADETECT_USE_END_USER": "A",
    #  },
    #  'result': {
    #      'WCONFIG($VALRPT)': [r'Validation\sReturn\sCode\s[=]\s8',
    #                          r'KD2_ADETECT_ENABLED\s+U',
    #                          r'KD2_ADETECT_MEMORY_SIZE\s+500',
    #                          r'KD2_ADETECT_MIN_COUNT\s+A',
    #                          r'KD2_ADETECT_USE_AUTH\s+A',
    #                          r'KD2_ADETECT_USE_CONNECT\s+A',
    #                          r'KD2_ADETECT_USE_CONNNAME\s+A',
    #                          r'KD2_ADETECT_USE_CORRID\s+A',
    #                          r'KD2_ADETECT_USE_END_USER\s+A',
    #                          r'KD2_ADETECT_USE_PLAN\s+A',
    #                          r'KD2_ADETECT_USE_TRANSACTION\s+A',
    #                          r'KD2_ADETECT_USE_WORKSTATION\s+A',
    #                            ],
    #    },
    # },
    'parm-712': {
        'parameters': {
            'KS3_NODEJS_HOME': '/rsusr/cnj/IBM/node-v6.14.4-os390-s390x',
            'KS3_AS_LISTENER_ADDR': 'localhost'
        },
        'result': {
            'WCONFIG($VALRPT)': r'Validation\sReturn\sCode\s[=]\s8'
        }
    },
    'parm-1042': {
        'removed_params': {
            'parameters': [],
            'masks_params': ['KI2_I1'],
        },
        'result': {
            'WCONFIG($VALRPT)': [r'Validation\sReturn\sCode\s[=]\s8',
                                 r'KI2_I101_ROW\s+\(null\)',
                                 r'KI2_I101_CLASSIC_IMSID\s+\(null\)',
                                 r'KI2_I101_CLASSIC_IMS_RESLIB\s+\(null\)']
        }
    }
}


@pytest.mark.parametrize("parameters, results, removed_params",
                         [(config_changes[i].get('parameters', {}), config_changes[i].get('result'),
                           config_changes[i].get('removed_params')) for i in config_changes])
def test_verify_parse_fail_with_incorrect_parameters(parameters, results, removed_params, zosmf):
    rte1 = Parmgen(username, password, hlq[0:hlq.rfind('.')], rte)
    rte1.save_config()
    try:
        if parameters:
            rte1.change_parameters(params=parameters)
        if removed_params:
            rte1.remove_parameters(removed_params=removed_params)
        rte1.logon()
        with pytest.raises(ParmException) as excinfo:
            # this is the last executed line inside "with"
            rte1.step_3_1_parse()
        assert 'RC code 0008 in' in str(excinfo.value)
        assert Parmgen.verify_values_in_datasets(results, zosmf, rte)
    finally:
        rte1.restore_config()
        rte1.logoff()
