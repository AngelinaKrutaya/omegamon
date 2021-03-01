from enum import Enum

BASE_LIBS = [
    'RKANCLI',
    'RKANCMD',
    'RKANDATR',
    'RKANEXEC',
    'RKANHENU',
    'RKANISP',
    'RKANMOD',
    'RKANMODL',
    'RKANMODP',
    'RKANMODR',
    'RKANOSRC',
    'RKANPAR',
    'RKANPENU',
    'RKANSAM',
    'RKANSAMF',
    'RKANSAMV',
    'RKANSQL',
    'RKANWENU',
    'RKNSLOCL',
    'RKOBDATF',
    'RKOBHELP',
    'RKOCHELP',
    'RKOCPROC',
    'RKOIHELP',
    'RKOIPROC',
    'RKOMHELP',
    'RKOMPROC',
    'RKO2DATA',
    'RKO2DBRM',
    'RKO2EXEC',
    'RKO2HELP',
    'RKO2MENU',
    'RKO2PENU',
    'RKO2PROC',
    'RKO2SAMP',
    'RKO2SLIB',
    'RKO2TENU',
]


class RteType(Enum):
    SHARED = 1
    FULL = 2
