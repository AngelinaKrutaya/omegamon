from libs.rte import RteType

rtes = {
    'ite1':
        {
            'hostname': 'rsd1',
            'tems': 'ite1ds',
            'tom_applid': 'ite1obap',
            'hub_name': 'HUB_WALDEVITMZQA01',
            'rte_hlq': 'itm.ite.ite1',
            'tom_stc': 'ite1tom',
            'type': RteType.SHARED,
            'clist': 'ITM.ITE.QA.CLIST',
            'shared_ds': 'ITM.ITE.BASE',
        },
    'ite2':
        {
            'hostname': 'rsd2',
            'tems': 'ite2ds',
            'tom_applid': 'ite2obap',
            'hub_name': 'HUB_WALDEVITMZQA01',
            'rte_hlq': 'itm.ite.ite2',
            'shared_ds': 'itm.ite.base',
            'tom_stc': 'ite2tom',
            'type': RteType.SHARED,
        },
    'ite3':
        {
            'hostname': 'rsd3',
            'tems': 'ite3ds',
            'tom_applid': 'ite3obap',
            'hub_name': 'HUB_WALDEVITMZQA01',
            'rte_hlq': 'itm.ite.ite3',
            'tom_stc': 'ite3tom',
            'type': RteType.FULL,
        },
    'ite4':
        {
            'hostname': 'rsd4',
            'tems': 'ite4ds',
            'tom_applid': 'ite4obap',
            'hub_name': 'ITE4:CMS',
            'rte_hlq': 'itm.ite.ite4',
            'tems_http': '21020',
            'teps': 'waldevitmzqa03',
            'db2': 'ICD4',
        },
    'itp1':
        {
            'hostname': 'rsd2',
            'rte_hlq': 'itm.ite.itp1',
            'shared_ds': 'itm.ite.base',
            'rte_model': '@MDLRSB',
            'hlq': ' itm.ite',
            'type': RteType.SHARED,
            'rte_products': ['KC5', 'KDS', 'KD5', 'KGW', 'KI5', 'KJJ', 'KMQ', 'KM5', 'KN3', 'KOB', 'KQI', 'KS3']
        },
    'itp2':
        {
            'hostname': 'rsd2',
            'rte_hlq': 'itm.ite.itp2',
            'rte_model': '@MDLHF',
            'hlq': ' itm.ite',
            'type': RteType.FULL,
            'rte_products': ['KC5', 'KDS', 'KD5', 'KGW', 'KI5', 'KJJ', 'KMQ', 'KM5', 'KN3', 'KOB', 'KQI', 'KS3']
        },
    'itp3':
        {
            'hostname': 'rsd2',
            'rte_hlq': 'itm.ite.itp3',
            'type': RteType.FULL,
            'rte_model': '$MDLHFV',
            'rte_products': ['KC5', 'KDS', 'KD5', 'KGW', 'KI5', 'KJJ', 'KMQ', 'KM5', 'KN3', 'KOB', 'KQI', 'KS3']
        },
    'itp4':
        {
            'hostname': 'rsd2',
            'rte_hlq': 'itm.ite.itp4',
            'shared_ds': 'itm.ite.base',
            'type': RteType.SHARED,
            'vars': True,
            'rte_model': '$MDLRSBV',
            'rte_products': ['KC5', 'KDS', 'KD5', 'KGW', 'KI5', 'KJJ', 'KMQ', 'KM5', 'KN3', 'KOB', 'KQI', 'KS3']
        },
    'itp5': {
        'hostname': 'rsd2',
        'rte_hlq': 'itm.ite.plib.itp5',
        'gbl_hlq': 'itm.ite',
        'type': RteType.FULL,
        'vars': True,
        'rte_model': '$MDLHFV',
        'rte_products': ['KC5', 'KDS', 'KD5', 'KGW', 'KI5', 'KJJ', 'KMQ', 'KM5', 'KN3', 'KOB', 'KQI', 'KS3']
    },
    'itcc':
        {
            'hostname': 'rsd2',
            'rte_hlq': 'itm.itc.itcc',
            'tom_applid': 'itccobap',
            'rte_model': '@MDLHF',
            'type': RteType.SHARED,
            'rte_products': ['KC5', 'KDS', 'KM5', 'KOB']
        },
}
