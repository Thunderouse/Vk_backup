import requests
from tqdm import tqdm
from time import sleep
import os
from pprint import pprint


class VK:

    def __init__(self, access_token, user_id, album_id, version='5.131'):
        self.token = access_token
        self.id = user_id
        self.album_id = album_id
        self.version = version
        self.params = {'access_token': self.token, 'v': self.version}

    def _get_data(self):
        url = 'https://api.vk.com/method/photos.get'
        params = {'owner_id': self.id, "album_id": self.album_id, "extended": 1}
        response = requests.get(url, params={**self.params, **params})
        global vk_data
        vk_data = response.json()
        print('Получаем данные из профиля')
        vk_data_bar = [sleep(0.2) for i in tqdm(vk_data)]
        vk_data_bar_response = [sleep(0.2) for i in tqdm(vk_data['response'])]
        vk_data_bar_items = [sleep(0.2) for i in tqdm(vk_data['response']['items'])]
        return vk_data

    def _get_date(self):
        data = vk_data['response']['items']
        date_list = []
        item = 0
        for day in data:
            date = data[item]['date']
            date_list.append(date)
            item += 1
        print("Получаем информацию о датах")
        date_list_bar = [sleep(0.2) for i in tqdm(date_list)]
        return date_list

    def _get_likes(self):
        data = vk_data['response']['items']
        likes_list = []
        item = 0
        for like in data:
            likes = data[item]['likes']['count']
            likes_list.append(likes)
            item += 1
        print("Введите сколько записей вы хотите сохранить (записи выбираются по количеству лайков от "
              "большего к меньшему, по умолчанию 5)")
        count = input()
        count = int(count)
        if type(count) == int:
            most_likes = sorted(likes_list, reverse=True)[:int(count)]
        else:
            most_likes = sorted(likes_list, reverse=True)[:5]

        print("Получаем информацию о лайках")
        likes_list_bar = [sleep(0.2) for i in tqdm(most_likes)]
        return most_likes

    def _users_photos(self):
        vk_data = vk._get_data()
        data = vk_data['response']['items']
        date_list = vk._get_date()
        most_likes = vk._get_likes()
        likes_dict = {}
        url_list = []
        final_dict = {}
        x = 0
        like_number = 0
        for l in data:
            urls = [d['url'] for d in l['sizes'] if d['type'] == 'w']
            if len(urls) == 0:
                urls = [d['url'] for d in l['sizes'] if d['type'] == 'z']
            if len(urls) == 0:
                urls = [d['url'] for d in l['sizes'] if d['type'] == 'y']
            if len(urls) == 0:
                urls = [d['url'] for d in l['sizes'] if d['type'] == 'r']
            if len(urls) == 0:
                urls = [d['url'] for d in l['sizes'] if d['type'] == 'q']
            if l['likes']['count']:
                for like in most_likes:
                    x += 1
                    if like == l['likes']['count']:
                        for datee in date_list:
                            if l['date'] == datee:
                                likes_dict[like] = urls
                                url_list.append(urls)
                                final_dict[datee] = {like: urls}
                                like_number+=1
                                x = 0
        print("Загружаем фото на ваш ПК")
        photos_bar = [sleep(0.2) for i in tqdm(final_dict.items())]
        return final_dict

    def _create_directory_on_pc(self):
        directory_path = os.path.expanduser("~/Downloads")
        if os.path.exists(f"{directory_path}/Vk_backup"):
            print("Фото были загруженны на пк")
        else:
            os.mkdir(f"{directory_path}/Vk_backup")
            print("Папка для файлов создана, а фото будут загруженны в нее")
        return directory_path

    def download_photo_to_pc(self):
        photos_dict = vk._users_photos()
        vk._create_directory_on_pc()
        file_path = os.path.expanduser("~/Downloads")
        for date in photos_dict.keys():
            date_part = date
            for likes_urls in photos_dict[date]:
                likes_part = likes_urls
                urls = photos_dict[date][likes_urls]
                name = f"{likes_part}_{date_part}"
                for url in urls:
                    res = requests.get(url)
                    img = open(f"{file_path}/Vk_backup/{name}" + ".jpg", "wb")
                    img.write(res.content)
                    img.close()

        ya_disk.upload_photo()


class YandexDisk:
    def __init__(self, token: str):
        self.token = token

    def _create_folder(self):
        print("Создаем папку на вашем Яндекс диске")
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': f'OAuth {self.token}'}
        res = requests.put(f'https://cloud-api.yandex.net/v1/disk/resources?path=Vk_backup', headers=headers)
        if res.status_code == 201:
            print("Папка была создана")
        elif res.status_code == 409:
            print("Папка уже есть на вашем диске")
        else:
            res.raise_for_status()

    def upload_photo(self, replace=True):
        ya_disk._create_folder()
        path = os.path.expanduser("~/Downloads")
        file_list = os.listdir(f"{path}/Vk_backup")
        headers = {'Content-Type': 'application/json', 'Accept': 'application/json',
                   'Authorization': f'OAuth {self.token}'}
        URL = "https://cloud-api.yandex.net/v1/disk/resources"
        path_to_folder = f"{path}/Vk_backup/"
        print("Загружаем фото на Яндекс диск")
        for file in file_list:
            res = requests.get(f'{URL}/upload?path=Vk_backup/{file}&overwrite={replace}', headers=headers).json()
            final_path = path_to_folder + file
            with open(final_path, 'rb') as f:
                try:
                    requests.put(res['href'], files={'file': f})
                except KeyError:
                    print(res)
        photos_to_disk_bar = [sleep(0.2) for i in tqdm(file_list)]


if __name__ == "__main__":
    access_token = ''
    file_path = "Vk_Backup/"
    user_id = int(input("Введите ваш id в ВК (числовой)"))
    album_id = 'wall'
    ya_disk_token = input("Введите токен от вашего яндекс диска, на который вы хотите загрузить фото")
    global vk
    global ya_disk
    vk = VK(access_token, user_id, album_id)
    ya_disk = YandexDisk(ya_disk_token)
    vk.download_photo_to_pc()
