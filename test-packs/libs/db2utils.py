from taf.zos.py3270 import Emulator
from taf.zos.py3270 import keys


def classic_in_out_func(username, password, hostname, applid, ssid, security=True):
    em = Emulator(hostname, model=2, oversize=(24, 80))
    d = em.display

    try:
        welcome = d.find('===> Ex.: LOGON <userid>, TSO <userid>')
        if welcome:
            welcome.shift((1, 0))(f"L {applid} DATA='LROWS=9999,DB2={ssid}'", keys.ENTER, 240)
        if security:
            d(username, keys.NEWLINE)
            d(password, keys.ENTER)
        else:
            d(key=keys.ENTER, timeout=30)

        assert d.find('ZMENU    VTM')
        yield d
        d(key=keys.PF3)
        d('X', key=keys.ENTER)
    finally:
        em.disconnect()
        em.close()
