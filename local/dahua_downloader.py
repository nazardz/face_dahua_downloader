import time
import requests
from requests.auth import HTTPDigestAuth
# import tqdm
import os
import local.memory_check as mc


class DahuaDownloader(object):
    def __init__(self, dahua_ip, dahua_login, dahua_password, date_from, date_to, output_path, limit):
        """Constructor"""
        self.auth = HTTPDigestAuth(dahua_login, dahua_password)
        self.dahua_url_method = 'http://{}/cgi-bin/mediaFileFind.cgi'.format(dahua_ip)
        self.output_path = output_path
        self.dahua_ip = dahua_ip
        self.dahua_channel = 1
        self.date_from = date_from
        self.date_to = date_to
        self.limit = limit
        self.types = 'jpg'
        self.token = None

    def login_dahua(self):
        # print("[I] Trying to login {}".format(self.dahua_ip))
        while True:
            response = requests.get(url=self.dahua_url_method, auth=self.auth, params={'action': 'factory.create'})
            if response.status_code == 200:
                self.token = response.text[7:].strip()
                # print("[I] Login success! Got token: {}".format(self.token))
                if len(self.token) > 0:
                    # print("[I] Trying to find files in interval: {} - {}".format(self.date_from, self.date_to))
                    response = requests.get(auth=self.auth,
                                            url=self.dahua_url_method + f'?action=findFile&object={self.token}&'
                                                                        f'condition.Channel={self.dahua_channel}&'
                                                                        f'condition.StartTime={self.date_from}&'
                                                                        f'condition.EndTime={self.date_to}&'
                                                                        f'condition.Types[0]={self.types}')
                    if response.status_code == 200 and response.text[:2] == 'OK':
                        # print("[I] Find files success!")
                        return True
                    else:
                        # print("[W] Wrong response findFile method: " + response.text)
                        self.close_session()
                else:
                    print("[W] Wrong token: " + response.text)
                    return False
            else:
                print("[W] Wrong auth: " + response.text)
                return False

    def create_file_list(self):
        dahua_files = []
        more_files = True
        while more_files:
            response = requests.get(url=self.dahua_url_method, auth=self.auth,
                                    params={'action': 'findNextFile', 'object': self.token, 'count': '1'})
            if response.status_code == 200:
                file_info = response.text
                if file_info[:7] == "found=0":
                    more_files = False
                else:
                    if file_info[:6] == "found=":
                        file_items = dict(item.split("=") for item in file_info.split("\r\nitems[0]."))
                        if 'FilePath' in file_items and 'Length' in file_items:
                            file_name = file_items['FilePath']
                            file_length = file_items['Length']
                            dahua_files.append({'file_name': file_name,
                                                'file_length': file_length})
                        else:
                            print('[W] Wrong findNextFile method' + file_info)
                            pass
                    else:
                        print('[W] Wrong file_info response: ' + file_info)
                        break
            else:
                break
        return dahua_files

    def download_file(self, file_name, file_length, idx, list_count, root_path):
        rpc_dav_url = 'http://{}/cgi-bin/RPC_Loadfile{}'.format(self.dahua_ip, file_name)
        path_name = file_name.split('/')
        form = 'face' if idx % 2 != 0 else 'full'
        lit_0 = path_name[-6].replace("-", "_")
        lit_1 = path_name[-1].replace("]", "_", 3)[10:-4].replace("[", "").replace("]", "")
        abs_path = f'{lit_0}_{path_name[-3]}_{path_name[-2]}_{path_name[-1][:2]}_{lit_1}_{form}{path_name[-1][-4:]}'
        output_file_name = self.output_path + "/" + abs_path
        while True:
            while not mc.direcroty_size_check(root_path, self.limit):
                old_file = mc.oldest_file_in_tree(root_path)
                os.remove(old_file)
            try:
                if os.path.exists(output_file_name) and str(os.stat(output_file_name).st_size) == file_length:
                    # print("[I] File {} exists, skipping!".format(output_file_name))
                    pass
                else:
                    # print("[I] Downloading {} of {} to {}".format(idx + 1, list_count, file_name))
                    response = requests.get(rpc_dav_url, auth=self.auth, stream=True)
                    # total_size_in_bytes = int(response.headers.get('content-length', 0))
                    block_size = 1024  # 1 Kilobyte
                    # progress_bar = tqdm.tqdm(total=total_size_in_bytes, unit='iB', unit_scale=True)
                    with open(output_file_name, 'wb') as file:
                        for data in response.iter_content(block_size):
                            # progress_bar.update(len(data))
                            file.write(data)
                    # progress_bar.close()
                    # if total_size_in_bytes != 0 and progress_bar.n != total_size_in_bytes:
                    #     print("[E] Something went wrong")
                    #     pass
                break
            except Exception as e:
                # print(e)
                time.sleep(1)
        return output_file_name

    def close_session(self):
        requests.get(url=self.dahua_url_method, auth=self.auth, params={'action': 'close', 'object': self.token})
