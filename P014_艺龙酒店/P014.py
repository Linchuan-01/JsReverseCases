"""
目标平台：艺龙旅行网（同程旅行）
目标页面：https://www.elong.com/
数据接口：https://www.elong.com/tapi/v2/list
目标参数：

"""

import os
import csv
import yaml
import time
import uuid
import execjs
import hashlib
import requests
from loguru import logger
from urllib.parse import quote


class P014(object):
    """艺龙旅行网（同程旅行）"""

    BASE_URL = "https://www.ly.com/tapi/v2/list"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/146.0.0.0 Safari/537.36",
        "appfrom": "16",
        "lang": "zh-cn",
        "pagename": "hotellist",
        "timezone": "8",
        "tmapi-client": "epc",
    }

    def __init__(self):
        """
        初始化方法
        """
        filename = os.path.dirname(__file__)
        config = self._load_config(filename)
        self.pages = config["app"]["pages"]
        self.deviceid = config["app"]["deviceid"]
        self.timeout = config["app"]["timeout"]
        self.inDate = config["app"]["inDate"]
        self.outDate = config["app"]["outDate"]
        self.city = config["app"]["city"]
        self.csv_path = os.path.join(filename, config["app"]["csv_path"])
        self.cookies = config["cookie"]
        self.session = requests.session()
        self.session.cookies.update(self.cookies)
        self.headers = self.HEADERS
        self.headers["deviceid"] = self.deviceid
        self.traceToken = None
        self.seen_sha1 = set()
        self._load_existing_hashes()
        self.ctx = execjs.compile(self._load_JavaScript(filename))

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
                config = P014._deep_merge(config, yaml.safe_load(f) or {})
        return config

    @staticmethod
    def _deep_merge(base, override):
        """
        递归合并本地配置，覆盖同名键
        """
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = P014._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    @staticmethod
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P014.js')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JavaScript代码文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _content_sha1(item):
        """对酒店数据的核心字段做 SHA1 摘要，用于内容去重"""
        raw = f"{item['hotelId']}|{item['hotelName']}|{item['commentScore']}|{item['price']}|{item['hotelAddress']}"
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def _load_existing_hashes(self):
        """加载已有 CSV 中的 content_sha1，用于去重"""
        if os.path.exists(self.csv_path):
            try:
                with open(self.csv_path, "r", encoding="utf-8-sig") as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        h = row.get("content_sha1", "").strip()
                        if h:
                            self.seen_sha1.add(h)
                logger.info(f"已加载 {len(self.seen_sha1)} 条已有数据指纹")
            except Exception as e:
                logger.warning(f"加载已有数据失败: {e}")

    def save_to_csv(self, items_list):
        """将新增酒店数据追加写入 CSV"""
        file_exists = os.path.exists(self.csv_path)
        try:
            with open(self.csv_path, "a", encoding="utf-8-sig", newline="") as f:
                fieldnames = [
                    "hotelId", "hotelName", "commentScore", "price",
                    "hotelAddress", "hotel_traceToken", "content_sha1",
                ]
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                if not file_exists:
                    writer.writeheader()
                writer.writerows(items_list)
            logger.success(f"成功保存 {len(items_list)} 条数据到 {self.csv_path}")
        except Exception as e:
            logger.error(f"保存 CSV 失败: {e}")

    def _parse_data(self, data_info):
        """解析数据: SHA1 内容去重后写入 CSV, 并提取 traceToken 回传"""
        data_dict = data_info.get("data", {})
        hotelList = data_dict.get("hotelList", [])
        if not hotelList:
            logger.warning("当前页无酒店数据")
            return []

        new_items = []
        for hotel in hotelList:
            item = {
                "hotelId": str(hotel.get("hotelId") or ""),
                "hotelName": hotel.get("hotelName"),
                "commentScore": hotel.get("commentScore"),
                "price": hotel.get("price"),
                "hotelAddress": hotel.get("hotelAddress"),
                "hotel_traceToken": data_dict.get("traceToken"),
            }
            sha1 = self._content_sha1(item)
            if sha1 in self.seen_sha1:
                logger.debug(f"重复数据跳过: {item['hotelId']} {item['hotelName']}")
                continue
            item["content_sha1"] = sha1
            self.seen_sha1.add(sha1)
            new_items.append(item)
            logger.success(
                f"{item['hotelId']} | {item['hotelName']} | {item['commentScore']} | {item['price']} | {item['hotelAddress']}")
        new_trace = data_dict.get("traceToken")
        if new_trace:
            self.traceToken = new_trace
            logger.info(f"traceToken 已更新: {new_trace}")
        if new_items:
            self.save_to_csv(new_items)
        return [i["hotelId"] for i in new_items]

    def _set_headers(self, params):
        """设置动态请求头: Referer 随 params 变化 + user-dun (JS 指纹) + traceid (UUID)"""
        traceid = str(uuid.uuid4())
        ref_params = {k: params[k] for k in ("city", "inDate", "outDate", "filterList", "placename") if k in params}
        ref_query = "&".join(f"{k}={v}" for k, v in ref_params.items())
        referer = f"https://www.ly.com/hotel/hotellist?{ref_query}"
        self.session.headers["Referer"] = referer
        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        new_url = f"{self.BASE_URL}?{query_string}"
        user_dun = self.ctx.call("get_user_dun", new_url)
        self.session.headers["user-dun"] = user_dun
        self.session.headers["traceid"] = traceid
        logger.info(f"User-Dun 设置成功 | Referer: {referer}")

    def _fetch_data(self, page):
        """请求酒店列表页数据"""
        params = {
            "city": self.city,
            "inDate": self.inDate,
            "outDate": self.outDate,
            "filterList": "8888_1",
            "placename": "",
            "intl": "0",
            "pageIndex": str(page),
            "pageSize": "20"
        }
        if self.traceToken:
            params["traceToken"] = quote(self.traceToken)
        try:
            self._set_headers(params)
            response = self.session.get(self.BASE_URL, params=params, timeout=self.timeout, headers=self.headers)
            return response.json()
        except Exception as e:
            logger.error(f"请求第 {page} 页失败: {e}")
            return {"data": {"hotelList": [], "traceToken": None}}

    def run(self):
        """
        主方法入口
        """
        empty_count = 0
        for page in range(0, self.pages):
            try:
                response_json = self._fetch_data(page)
                new_ids = self._parse_data(response_json)
                if not response_json.get("data", {}).get("hotelList"):
                    empty_count += 1
                    logger.warning(f"第 {page + 1} 页无数据 (连续{empty_count}页)")
                    if empty_count >= 5:
                        logger.info("连续5页无数据，停止翻页")
                        break
                    continue
                empty_count = 0
                logger.info(f"第 {page + 1} 页完成，新增 {len(new_ids)} 条")
                time.sleep(1)
            except Exception as e:
                logger.error(f"请求第 {page + 1} 页失败: {e}")


if __name__ == '__main__':
    p014 = P014()
    p014.run()
