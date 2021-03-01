import logging

import pytest
from taf.text import Text

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


def test_parametrize():
    jcl = \
    """
    //HSF1010 JOB  'ACCT#','<UNAME>',
    //       MSGCLASS=K,NOTIFY=SDSF,CLASS=A,USER=<UNAME>
    //STEP2 EXEC PGM=SDSF,PARM='++20,500'
    //ISFOUT DD SYSOUT=A
    //ISFIN DD *
    """

    params = {'<UNAME>': 'myname',
              'HSF1010': 'HSF1111',
              'SYSOUT=A': 'SYSOUT=B',
              }

    new_jcl = Text(jcl).parametrize(params)

    logger.info(jcl)
    logger.info(new_jcl)

    assert 'myname' in new_jcl
    assert 'SYSOUT=B' in new_jcl
