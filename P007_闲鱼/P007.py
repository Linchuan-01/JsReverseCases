"""
目标平台：咸鱼二手交易平台
目标页面：https://www.goofish.com/
数据接口：https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/
目标参数：
    查询字符串：sign签名
"""
import os
import yaml
import time
import json
import hashlib
import requests
from loguru import logger
from datetime import datetime
from urllib.parse import unquote


class P007(object):
    """咸鱼二手交易苹果"""

    BASE_URL = "https://h5api.m.goofish.com/h5/mtop.taobao.idlemtopsearch.pc.search/1.0/"
    HEADERS = {
        "content-type": "application/x-www-form-urlencoded",
        "referer": "https://www.goofish.com/",
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0"
    }
    def __init__(self):
        """
        初始化方法
        """
        self.session = requests.session()
        self.headers = self.HEADERS
        self.timestamp = str(int(time.time() * 1000))
        config = self._load_config(os.path.dirname(__file__))
        self.session.cookies.update(config.get("cookie") or {})
        self.keyword = config["app"]["keyword"]
        self.pages = config["app"]["pages"]
        self.appKey = config["app"]["appKey"]

    @staticmethod
    def _load_config(filename):
        """
        加载配置文件
        :return: 配置数据
        """
        path = os.path.join(filename, "config.yaml")
        if not os.path.exists(path):
            raise FileNotFoundError(f"配置文件不存在：{path}")
        with open(path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
        local_path = os.path.join(filename, "config.local.yaml")
        if os.path.exists(local_path):
            with open(local_path, "r", encoding="utf-8") as f:
                config = P007._deep_merge(config, yaml.safe_load(f) or {})
        return config

    @staticmethod
    def _deep_merge(base, override):
        """
        递归合并本地配置，覆盖同名键
        """
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = P007._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _parse_data(json_data):
        """
        解析数据
        :param json_data:
        :return:
        """
        datas = json_data["data"]["resultList"]
        items = []
        for data in datas:
            main = data.get("data", {}).get("item", {}).get("main")
            ex = main["exContent"]
            args = main["clickParam"]["args"]
            tags = [t["data"]["content"] for row in ex.get("fishTags", {}).values() for t in row.get("tagList", []) if
                    t.get("data", {}).get("content")]
            ts = args.get("publishTime")
            info = {
                "id": ex["itemId"],
                "title": ex["title"][:40],
                "price": "".join(p["text"] for p in ex["price"]),
                "area": ex["area"],
                "seller": ex.get("userNickName", ""),
                "publish": datetime.fromtimestamp(int(ts) / 1000).strftime("%m-%d %H:%M") if ts else "",
                "pic": ex.get("picUrl", ""),
                "tags": tags,
                "keyword": unquote(args["q"]),
                "page": args["page"],
                "target": main["targetUrl"],
            }
            items.append(info)
            logger.info(
                f"item_id：{info['id']} | title：{info['title']} | price：{info['price']} | area：{info['area']} | seller：{info['seller']} | publish：{info['publish']} | pic：{info['pic']} | tags：{info['tags']} | keyword：{info['keyword']} | page：{info['page']} | target：{info['target']}")
        return items

    def _get_m_h5_tk(self, params, data):
        """
        获取_m_h5_tk参数
        :param params:
        :param data:
        :return:
        """
        response = self.session.post(url=self.BASE_URL, data=data, headers=self.headers, params=params)
        _m_h5_tk = response.cookies.get("_m_h5_tk").split("_")[0]
        return _m_h5_tk

    def _gen_sign(self, _m_h5_tk_enc, data, appkid):
        """
        计算sign签名
        :param appkid:
        :param data:
        :param _m_h5_tk_enc:
        :return:
        """
        h = _m_h5_tk_enc + "&" + self.timestamp + "&" + appkid + "&" + data
        sign = hashlib.md5(h.encode("utf-8")).hexdigest()
        return sign

    def _fetch_data(self, page):
        """
        发送网络请求，获取响应
        :param page: 页码
        :return:
        """
        params = {
            "jsv": "2.7.2",
            "appKey": self.appKey,
            "v": "1.0",
            "type": "originaljson",
            "accountSite": "xianyu",
            "dataType": "json",
            "timeout": "20000",
            "api": "mtop.taobao.idlemtopsearch.pc.search",
            "sessionOption": "AutoLoginOnly",
            "dangerouslySetWindvaneParams": "[object Object]",
            "spm_cnt": "a21ybx.search.0.0",
            "spm_pre": "a21ybx.search.searchInput.0"
        }
        payload = {
            "pageNumber": page,
            "keyword": self.keyword,
            "fromFilter": False,
            "rowsPerPage": 30,
            "sortValue": "",
            "sortField": "",
            "customDistance": "",
            "gps": "",
            "propValueStr": {},
            "customGps": "",
            "searchReqFromPage": "pcSearch",
            "extraFilterValue": "{}",
            "userPositionJson": "{}"
        }
        data = {
            'data': json.dumps(payload, separators=(',', ':'))
        }
        _m_h5_tk_enc = self._get_m_h5_tk(params, data)
        sign = self._gen_sign(_m_h5_tk_enc, data["data"], params["appKey"])
        params["sign"] = sign
        params["t"] = self.timestamp
        response = self.session.post(url=self.BASE_URL, data=data, headers=self.headers, params=params)
        return response.json()

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            json_data = self._fetch_data(page)
            items = self._parse_data(json_data)
            logger.info(f"page：{page} | items：{items}" + "\n")


if __name__ == '__main__':
    p007 = P007()
    p007.run()
