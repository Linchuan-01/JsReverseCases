"""
目标平台：哲风壁纸
目标页面：https://www.haowallpaper.com/homeView?page=2
数据接口：https://haowallpaper.com/link/pc/wallpaper/wallpaperList
目标参数：
    请求体：data参数
"""
import base64
import json
import os
from io import BytesIO

import yaml
import execjs
import requests
from PIL import Image
from loguru import logger
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad


class P004(object):
    """哲风壁纸x"""

    KEY = "68zhehao2O776519"
    IV = "aa176b7519e84710"
    BASE_URL = "https://haowallpaper.com/link/pc/wallpaper/wallpaperList"
    HEADERS = {
        "referer": "https://www.haowallpaper.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36"
    }

    def __init__(self):
        """
        初始化方法
        """
        self.headers = self.HEADERS
        filename = os.path.dirname(__file__)
        config = self._load_config(filename)
        self.pages = config['app']['pages']
        self.SAVE_DIR = filename + "\\" + config['app']['save_dir']
        if not os.path.exists(self.SAVE_DIR):
            os.makedirs(self.SAVE_DIR)
        self.wpType = config['app']['wpType']

    @staticmethod
    def _load_config(filename, env=None):
        """
        加载配置文件
        :return: 配置数据
        """
        filename = os.path.join(filename, 'config.yaml')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"配置文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        return config

    @classmethod
    def aes_encrypt(cls, plain_text):
        """AES加密函数"""
        key_bytes = cls.KEY.encode('utf-8')
        iv_bytes = cls.IV.encode('utf-8')
        data_bytes = plain_text.encode('utf-8')
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        padded_data = pad(data_bytes, AES.block_size)
        encrypted = cipher.encrypt(padded_data)
        return base64.b64encode(encrypted).decode('utf-8')

    @classmethod
    def aes_decrypt(cls, cipher_text):
        """AES解密函数"""
        key_bytes = cls.KEY.encode('utf-8')
        iv_bytes = cls.IV.encode('utf-8')
        encrypted_data = base64.b64decode(cipher_text)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        decrypted = cipher.decrypt(encrypted_data)
        unpadded = unpad(decrypted, AES.block_size).decode('utf-8')
        null_pos = unpadded.find('\0')
        if null_pos != -1:
            unpadded = unpadded[:null_pos]
        return unpadded

    @staticmethod
    def parse_data(json_data):
        """解析数据，拿到图片地址"""
        data_list = json_data["list"]
        fileId_url_dict = dict()
        for data in data_list:
            fileId = data["fileId"]
            fileId_url = "https://haowallpaper.com/link//common/file/getCroppingImg/" + fileId
            fileId_url_dict[fileId] = fileId_url
        return fileId_url_dict

    def _fetch_data(self, page):
        """
        发送网络请求，获取响应
        :param page:
        :return:
        """
        dec_data = {"page": f"{page}", "sortType": 3, "rows": 12, "isFavorites": False, "wpType": self.wpType}
        enc_data = P004.aes_encrypt(json.dumps(dec_data, separators=(',', ':')))
        params = {"data": enc_data}
        response = requests.get(self.BASE_URL, headers=self.headers, params=params).json()
        data = response["data"]
        dec_data = P004.aes_decrypt(data)
        return json.loads(dec_data)

    def download_images(self, fileId_url_dict):
        """下载图片"""
        for fileId_path, fileId_url in fileId_url_dict.items():
            try:
                response = requests.get(fileId_url, timeout=10)
                img = Image.open(BytesIO(response.content))
                save_path = os.path.join(self.SAVE_DIR, f"{fileId_path}.png")
                img.save(save_path)
                logger.success(f"图片已保存：{save_path} | 图片链接：{fileId_url}")
            except Exception as e:
                logger.error(f"下载失败 {fileId_path}：{e}")

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            json_data = self._fetch_data(page)
            fileId_url_dict = self.parse_data(json_data)
            self.download_images(fileId_url_dict)


if __name__ == '__main__':
    p004 = P004()
    p004.run()
