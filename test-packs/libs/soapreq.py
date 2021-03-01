import requests
from libs.creds import *


class SoapException(Exception):
    def __init__(self, *args):
        if args:
            self.message = args[0]
        else:
            self.message = None

    def __str__(self):
        if self.message:
            return 'SoapException, {0} '.format(self.message)
        else:
            return 'SoapException has been raised'


class SoapReq:
    HEADERS = {'content-type': 'text/xml'}

    def __init__(self, hostname: str, port: int, user_=username, password_=password):
        self._user = user_
        self._password = password_
        self.url = f"http://{hostname}:{port}///cms/soap"

    def run(self, soap_req):
        body = f"""<SOAP-ENV:Envelope xmlns:SOAP-ENV="http://schemas.xmlsoap.org/soap/envelope/" 
            xmlns:soap="http://schemas.xmlsoap.org/wsdl/soap/" >
            <SOAP-ENV:Body>{soap_req}</SOAP-ENV:Body>
            </SOAP-ENV:Envelope>"""
        response = requests.post(self.url, data=body, headers=self.HEADERS)
        res = response.content.decode('UTF-8', 'ignore')
        # print(res)
        if '</SOAP-CHK:Success></SOAP-ENV:Body></SOAP-ENV:Envelope>' in res:
            return res
        else:
            raise SoapException(res)

    def get(self, soap_req):
        soap_req = f'<CT_Get><userid>{self._user}</userid><password>{self._password}</password>' + soap_req + '</CT_Get>'
        return self.run(soap_req)

    def alert(self, sit_name, source, message, item_id='item-id', severity='1', category='Critical'):
        soap_req = f'''
            <CT_Alert><hub>SOAP</hub><userid>{self._user}</userid><password>{self._password}</password>
        <name>{sit_name}</name><source>{source}</source>
        <data>
        <Universal_Messages.Message_Text>"{message}"</Universal_Messages.Message_Text>
        <Universal_Messages.Message_Severity>{severity}</Universal_Messages.Message_Severity>
        <Universal_Messages.Category>{category}</Universal_Messages.Category>
        </data><item>{item_id}</item></CT_Alert>
        '''
        return self.run(soap_req)

    def reset(self, sit_name, source, item_id='item-id'):
        soap_req = f'''
        <CT_Reset><hub>SOAP</hub><userid>{self._user}</userid><password>{self._password}</password>
        <name>{sit_name}</name><source>{source}</source>
        <item>{item_id}</item></CT_Reset>
        '''
        return self.run(soap_req)

