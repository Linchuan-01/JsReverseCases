"""
目标平台：7881账号交易平台
目标页面：https://search.7881.com/A5776-100003-0-0-0.html?pageNum=1
数据接口：https://gw.7881.com/goods-service-api/api/goods/list
目标参数：
    请求头：lb-sign、lb-timestamp
"""
import os
import yaml
import json
import time
import hashlib
import requests
from loguru import logger


class P003(object):
    """7881账号交易平台"""

    BASE_URL = "https://gw.7881.com/goods-service-api/api/goods/list"
    HEADERS = {
        "Content-Type": "application/json",
        "Referer": "https://search.7881.com/",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36",
    }

    def __init__(self):
        """
        初始化方法
        """
        self.headers = self.HEADERS
        filename = os.path.dirname(__file__)
        config = self._load_config(filename)
        self.gameId = config['app']['gameId']
        self.gtid = config['app']['gtid']
        self.pages = config['app']['pages']

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

    @staticmethod
    def _parse_data(json_data):
        """
        解析数据
        :param json_data: 接口返回的响应数据
        :return: 解析后的数据
        """
        items = list()
        datas = json_data.get("body", {}).get("results", [])
        for data in datas:
            item = dict()
            goodsId = data.get("goodsId")
            gameId = data.get("gameId")
            gameName = data.get("gameName")
            title = data.get("title")
            price = data.get("price")
            subTitlePc = data.get("subTitlePc")
            createtime = data.get("createtime")
            detailLink = f"https://search.7881.com/{goodsId}.html"
            item["goodsId"] = goodsId
            item["gameId"] = gameId
            item["gameName"] = gameName
            item["title"] = title
            item["price"] = price
            item["subTitlePc"] = subTitlePc
            item["createtime"] = createtime
            item["detailLink"] = detailLink
            items.append(item)
            logger.info(f"数据解析成功：{item}")
        return items

    @staticmethod
    def _encrypt_hash(_string):
        """
        哈希签名
        :param _string:
        :return:
        """
        md5_hash = hashlib.md5()
        md5_hash.update(_string.encode("utf-8"))
        return md5_hash.hexdigest()

    def _generate_Signature(self, _paramObj):
        """
        生成签名参数
        """
        lb_timestamp = str(int(round(time.time() * 1000)))
        pubKey = self._encrypt_hash("".join(reversed("5c2c538a3937c6db2d04bce3d03bbe88bl")) + lb_timestamp)
        encryObj = dict()
        encryObj["lb-timestamp"] = lb_timestamp
        encryObj["lb-sign"] = self._encrypt_hash(pubKey + _paramObj)
        return encryObj

    def _fetch_data(self, page: int, pageSize: int = 30):
        """
        向接口发送网络请求获取响应数据
        :param page: 页码
        :return: 响应数据
        """
        json_data = {
            "marketRequestSource": "search",
            "sellerType": "C",
            "gameId": self.gameId,
            "gtid": self.gtid,
            "tradePlace": "0",
            "goodsSortType": "6",
            "extendAttrList": [],
            "pageNum": page,
            "pageSize": pageSize,
        }
        json_data_str = json.dumps(json_data, separators=(',', ':'))
        self.headers.update(self._generate_Signature(json_data_str))
        response = requests.post(self.BASE_URL, headers=self.headers, data=json_data_str)
        return response.json()

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            json_data = self._fetch_data(page)
            items = self._parse_data(json_data)
            logger.info(f"{'=' * 50}第{page}页采集完成{'=' * 50}，共 {len(items)} 条" + "\n")


if __name__ == '__main__':
    p003 = P003()
    p003.run()
