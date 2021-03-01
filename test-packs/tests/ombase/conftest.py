from taf.zos.zosmflib import zOSMFConnector
from libs.creds import *

#     """
#     This needs for TSO/ISPF tests after reIPL
#     """
z = zOSMFConnector('rsd1', username, password)
z.issue_command('VARY NET,ACT,ID=KOBVT1AP')

