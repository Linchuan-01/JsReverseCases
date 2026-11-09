"""
目标平台：螃蟹账号交易平台
目标页面：https://www.pxb7.com/buy/10013/1?keyword=%E7%8E%8B%E8%80%85%E8%8D%A3%E8%80%80&searchType=%E5%8E%86%E5%8F%B2%E6%90%9C%E7%B4%A2
数据接口：https://api-pc.pxb7.com/api/bff/web/product/search/productPage
目标参数：
    查询字符串参数：timestamp__1366
"""
import os
import re
import yaml
import json
import time
import redis
import random
import execjs
import pymysql
import requests
from loguru import logger


class P001(object):
    """螃蟹账号交易平台"""

    BASE_URL = "https://api-pc.pxb7.com/api/bff/web/product/search/productPage"
    HEADERS = {
        'Referer': 'https://www.pxb7.com/',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0.0.0 Safari/537.36',
        'content-type': 'application/json',
        'os_type': '5',
        'px-authorization-merchant': '',
        'px-authorization-user': '',
    }
    DEFAULT_REDIS_KEY = "pxb7:product_ids"
    DEFAULT_TABLE = "pxb7_product"

    def __init__(self):
        """
        初始化方法
        """
        self.headers = self.HEADERS
        self.cookies = dict()
        self.renderData = dict()

        filename = os.path.dirname(__file__)
        config = self._load_config(filename)
        self._mysql_config = config.get("mysql", {})
        self._redis_config = config.get("redis", {})
        self.redis_key = self._redis_config.get("dedup_key") or self.DEFAULT_REDIS_KEY
        self.table = self._mysql_config.get("table") or self.DEFAULT_TABLE
        self.conn = None
        self.rds = None
        self.ctx = execjs.compile(self._load_JavaScript(filename))
        self.headers['device_id'] = config['app']['device_id']
        self.headers['gio_device'] = config['app']['gio_device']
        self._gameId = config['app']['gameId']
        self.pages = config['app']['pages']

    def _connect_mysql(self):
        """
        连接MySQL数据库
        :return:
        """
        conf = self._mysql_config
        self.conn = pymysql.connect(
            host=conf.get("host", "127.0.0.1"),
            port=int(conf.get("port", 3306)),
            user=conf.get("user", "root"),
            password=conf.get("password", ""),
            database=conf.get("database", "crawler"),
            charset=conf.get("charset", "utf8mb4"),
            connect_timeout=int(conf.get("timeout", 10)),
            autocommit=False,
        )
        self._create_table()
        logger.info(f"MySQL 连接成功：{conf.get('host')}:{conf.get('port')}/{conf.get('database')}")

    def _connect_redis(self):
        """
        连接Redis数据库
        :return:
        """
        conf = self._redis_config
        try:
            rds = redis.Redis(
                host=conf.get("host", "127.0.0.1"),
                port=int(conf.get("port", 6379)),
                password=conf.get("password") or None,
                db=int(conf.get("db", 0)),
                decode_responses=True,
                protocol=int(conf.get("protocol", 2)),
                socket_connect_timeout=3,
                socket_timeout=3,
            )
            rds.ping()
            self.rds = rds
            logger.info(f"Redis 连接成功：{conf.get('host')}:{conf.get('port')} db={conf.get('db', 0)}，去重 key={self.redis_key}")
        except Exception as exc:
            self.rds = None
            logger.warning(f"Redis 连接失败，本次仅依赖 MySQL 唯一键去重：{exc}")

    def _create_table(self):
        """
        创建数据表（不存在时）
        """
        create_sql = f"""
           CREATE TABLE IF NOT EXISTS `{self.table}` (
               `id` BIGINT UNSIGNED NOT NULL AUTO_INCREMENT COMMENT '自增主键',
               `game_id` VARCHAR(32) NOT NULL DEFAULT '' COMMENT '游戏ID',
               `product_id` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '商品ID',
               `product_unique_no` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '商品唯一编号',
               `game_name` VARCHAR(128) NOT NULL DEFAULT '' COMMENT '游戏名称',
               `price` DECIMAL(12, 2) NOT NULL DEFAULT 0.00 COMMENT '价格（元）',
               `attr_name_list` MEDIUMTEXT COMMENT '属性列表（JSON）',
               `small_img_show_title` VARCHAR(512) NOT NULL DEFAULT '' COMMENT '图片展示标题',
               `show_title` MEDIUMTEXT COMMENT '展示标题',
               `create_time` VARCHAR(64) NOT NULL DEFAULT '' COMMENT '商品创建时间（原始值）',
               `detail_link` VARCHAR(255) NOT NULL DEFAULT '' COMMENT '详情链接',
               `crawl_time` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '采集时间',
               PRIMARY KEY (`id`),
               UNIQUE KEY `uk_product_id` (`product_id`),
               KEY `idx_game_id` (`game_id`),
               KEY `idx_create_time` (`create_time`)
           ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COMMENT='螃蟹账号交易平台商品数据';
           """
        with self.conn.cursor() as cursor:
            cursor.execute(create_sql)
        self.conn.commit()

    def _is_new(self, item):
        """
        Redis 判重
        :return: True 表示新数据；Redis 不可用时返回 True，由 MySQL 唯一键兜底
        """
        if self.rds is None:
            return True
        return bool(self.rds.sadd(self.redis_key, str(item["productId"])))

    def _sync_redis_from_mysql(self):
        """
        启动时把 MySQL 已有的 product_id 预热进 Redis，
        避免因 Redis 被清空/换 key 导致去重状态与 MySQL 不同步
        """
        if self.rds is None:
            return
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(f"SELECT `product_id` FROM `{self.table}`")
                ids = [row[0] for row in cursor.fetchall()]
            if ids:
                self.rds.sadd(self.redis_key, *ids)
                logger.info(f"Redis 去重预热完成：从 MySQL 同步 {len(ids)} 个 product_id")
        except Exception as exc:
            logger.warning(f"Redis 去重预热失败（不影响运行）：{exc}")

    def _rollback_redis(self, items):
        """
        入库失败时回滚 Redis 去重标记，保证下次采集可以重试
        """
        if self.rds is None or not items:
            return
        try:
            self.rds.srem(
                self.redis_key, *[str(item["productId"]) for item in items]
            )
        except Exception as exc:
            logger.warning(f"Redis 去重标记回滚失败：{exc}")

    def _save_items(self, items):
        """
        保存数据
        :param items: 解析后的数据列表
        :return:
        """
        if not items:
            return 0, 0

        # 过滤无效数据
        valid_items = [item for item in items if item.get("productId")]
        invalid_count = len(items) - len(valid_items)
        if invalid_count:
            logger.warning(f"跳过 {invalid_count} 条缺少 productId 的数据")

        new_items = []
        try:
            for item in valid_items:
                if self._is_new(item):
                    new_items.append(item)
        except Exception as exc:
            self._rollback_redis(valid_items)
            raise
        skipped = len(valid_items) - len(new_items)
        if not new_items:
            return 0, skipped

        rows = list()
        for item in new_items:
            rows.append((
                item["_gameId"],
                item["productId"],
                item["productUniqueNo"],
                item["gameName"],
                item["price"],
                json.dumps(item["attrNameList"], ensure_ascii=False),
                item["smallImgShowTitle"],
                item["showTitle"],
                item["createTime"],
                item["detailLink"],
            ))
            logger.success(f"MySQL 正在写入商品数据：{item}")
        return self._insert(rows, new_items, skipped)

    def _insert(self, rows, new_items, skipped):
        """
        插入数据
        :return:
        """
        insert_sql = f"""
        INSERT INTO `{self.table}` (
            `game_id`, `product_id`, `product_unique_no`, `game_name`, `price`, `attr_name_list`, `small_img_show_title`, `show_title`, `create_time`, `detail_link`
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        try:
            with self.conn.cursor() as cursor:
                cursor.executemany(insert_sql, rows)
            self.conn.commit()
            return len(new_items), skipped
        except pymysql.err.IntegrityError:
            # Redis 判重与 MySQL 唯一键状态不同步：改用 INSERT IGNORE 逐批写入，
            # 已存在的记录跳过，不会导致整批失败
            logger.warning("MySQL 唯一键冲突（Redis 去重与 MySQL 不同步），降级为 INSERT IGNORE 写入")
            self.conn.rollback()
            insert_ignore_sql = insert_sql.replace("INSERT INTO", "INSERT IGNORE INTO")
            inserted = 0
            try:
                with self.conn.cursor() as cursor:
                    # executemany 每批最多 16 条，逐行 IGNORE 即可，行数不多性能无碍
                    for row in rows:
                        cursor.execute(insert_ignore_sql, row)
                        inserted += cursor.rowcount
                self.conn.commit()
                logger.info(f"IGNORE 写入完成：实际新增 {inserted} 条，重复跳过 {len(rows) - inserted} 条")
            except Exception as exc:
                self.conn.rollback()
                self._rollback_redis(new_items)
                raise exc
            return inserted, skipped + (len(rows) - inserted)
        except Exception:
            self.conn.rollback()
            self._rollback_redis(new_items)
            raise


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
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P001.js')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JavaScript代码文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _parse_data(json_data):
        """
        解析数据
        :param json_data: 接口返回的JSON数据
        :return:
        """
        items = list()
        datas = json_data.get("data", {}).get("list", [])
        for data in datas:
            item = dict()
            _gameId = data.get("productBasicInfo", {}).get("gameId", "")
            productId = data.get("productBasicInfo", {}).get("productId", "")
            productUniqueNo = data.get("productBasicInfo", {}).get("productUniqueNo", "")
            gameName = data.get("productBasicInfo", {}).get("gameName", "")
            price = data.get("productPriceInfo", {}).get("price", 0) / 100
            attrNameList = data.get("attrNameList", [])
            smallImgShowTitle = data.get("productBasicInfo", {}).get("smallImgShowTitle", "")
            showTitle = data.get("productBasicInfo", {}).get("showTitle", "")
            createTime = data.get("productBasicInfo", {}).get("createTime", "")
            detailLink = "https://www.pxb7.com/product/{}/1".format(productId)
            item["_gameId"] = _gameId
            item["productId"] = productId
            item["productUniqueNo"] = productUniqueNo
            item["gameName"] = gameName
            item["price"] = price
            item["attrNameList"] = attrNameList
            item["smallImgShowTitle"] = smallImgShowTitle
            item["showTitle"] = showTitle
            item["createTime"] = createTime
            item["detailLink"] = detailLink
            items.append(item)
        return items

    def _get_dynamic_token(self):
        """
        获取动态令牌
        :return:
        """
        response = requests.get(self.BASE_URL, headers=self.headers)
        self.renderData["_waf_bd8ce2ce37"] = re.search(r'_waf_bd8ce2ce37":"(.*?)"}<', response.text, re.S).group(1)
        self.renderData["_waf_a86dfdc5f2"] = int(time.time() * 1000)
        self.cookies["acw_tc"] = response.cookies.get("acw_tc")
        logger.info(f"动态令牌获取成功：{self.renderData}")

    def _get_timestamp__1366(self, json_data_str: str):
        """
        获取timestamp__1366
        :return:
        """
        timestamp__1366 = self.ctx.call("LK", self.BASE_URL, json_data_str, "POST", self.renderData)
        logger.info(f"timestamp__1366：{timestamp__1366}")
        return timestamp__1366

    def _fetch_data(self, pageIndex: int, pageSize: int = 16):
        """
        发送网络请求，获取数据
        :param page: 页码
        :return: 接口响应
        """
        params = dict()
        json_data = {
            "query": "",
            "gameId": self._gameId,
            "pageIndex": pageIndex,
            "pageSize": pageSize,
            "bizProd": 1,
            "type": "1",
            "posType": 1,
            "filterDTOList": [],
            "sortAttrId": "",
            "mineFav": False,
            "sortType": 2,
            "combineFilterList": [],
            "pageToken": "TIdWSiXvxeAL4n7OdzUHN1jYFegTwJMRqj_7SxAKg2g"
        }
        json_data_str = json.dumps(json_data, separators=(',', ':'))
        timestamp__1366 = self._get_timestamp__1366(json_data_str)
        params['timestamp__1366'] = timestamp__1366
        response = requests.post(self.BASE_URL, headers=self.headers, cookies=self.cookies, data=json_data_str,
                                 params=params)
        return response.json()

    def _close(self):
        """
        关闭连接
        """
        if self.conn:
            self.conn.close()
        if self.rds:
            self.rds.close()

    def main(self):
        """
        主方法入口
        """
        self._connect_mysql()
        self._connect_redis()
        self._sync_redis_from_mysql()
        self._get_dynamic_token()
        total_new = 0
        total_skip = 0
        try:
            for page in range(1, self.pages + 1):
                json_data = self._fetch_data(page)
                items = self._parse_data(json_data)
                new_count, skip_count = self._save_items(items)
                total_new += new_count
                total_skip += skip_count
                logger.info(f"{'=' * 50}第{page}页采集完成{'=' * 50}，新增 {new_count} 条，去重跳过 {skip_count} 条" + "\n")
                time.sleep(random.randint(1, 3))
        finally:
            self._close()
            logger.info(f"采集结束：共新增 {total_new} 条，去重跳过 {total_skip} 条")


if __name__ == '__main__':
    p001 = P001()
    p001.main()
