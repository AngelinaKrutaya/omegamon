from os.path import basename, isfile
from os import listdir
import os


from taf.zos.common.dataset import Dataset


class Dataset_ext(Dataset):

    def get_session(self):
        return self.zo._zOSMFConnector__s


    def upload_ds_member(self, source: str, ds_name: str, recfm: str='FB', dsorg: str='PS', primary: int=1, secondary: int=5,
                  blksize: int=3200, lrecl: int=80, dirblk: int=10) -> tuple:
        """
        Works with Partitioned and Sequential Data Sets
        Uploads the dataset to remote z/os system from the local directory with files as members
        https://www.ibm.com/support/knowledgecenter/en/SSLTBW_2.1.0/com.ibm.zos.v2r1.izua700/IZUHPINFO_API_CreateDataSet.htm

        Data Set Options: https://www.ibm.com/support/knowledgecenter/en/SSLTBW_2.1.0/com.ibm.zos.v2r1.idad400/dcbparm.htm

        :param dsorg: PO/PS/DA - Data set organization (Partitioned/Sequential/Direct)
        :param recfm: F/FB/V/VB/U - Record format: F=fixed, V=variable, B=blocked, U=undefined
        :param source: for part. DS - Path to directory with files to upload, for seq. DS - path to file
        :param dest: Dataset name on remote z/OS
        :param dirblk: Number of directory blocks (ignored for sequential DS)
        :param lrecl: Record length
        :param blksize: Block size
        :param primary: Primary space allocation
        :param secondary: Secondary space allocation

        :return: tuple: (result_boolean, result_text)
        """
        url = self.zo.dsurl + ds_name
        if dsorg == 'PS':
            if not isfile(source):
                raise WriteDatasetError('Single file is the only supported source for writing to Sequential dataset')
            dirblk = 0
            rcode_ok = 204
        else:
            rcode_ok = 201
        data = {'recfm': recfm,
                'dsorg': dsorg,
                'primary': primary,
                'blksize': blksize,
                'secondary': secondary,
                'lrecl': lrecl,
                'dirblk': dirblk}

        # response = self.__s.post(url, json=data)
        # if response.status_code != 201:
        #     return False, 'cannot create a dataset: ' + str(response.status_code) + ': ' + json.loads(response.text)['message']

        dataset_contents = {}
        dataset_contents['seq'] = [i for i in open(source)]
        errors = []
        for i in dataset_contents.keys():
            header = {
                'Content-Type': 'text/plain; charset=UTF-8',
                'X-IBM-Data-Type': 'text'}
            # data = '\n'.join(dataset_contents[i])
            data = ''.join(dataset_contents[i])
            member_url = url
            response = self.get_session().put(member_url, data=data, headers=header)
            assert True
            self.zo._check_rest_rc(response)
            if response.status_code != rcode_ok:
                errors.append(i + ', ' + str(response.status_code) + ', ' + response.text)
        if len(errors) == 0:
            return True, 'dataset was uploaded with all members'
        else:
            return False, 'dataset was created but not all members were uploaded. got errors on following members: ' + ','.join(errors)




