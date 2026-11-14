"""
目标平台：携程酒店
目标页面：https://hotels.ctrip.com/hotels/list
数据接口：https://m.ctrip.com/restapi/soa2/34951/fetchHotelList
目标参数：
    请求头：phantom-token
"""
import os
import execjs
import requests
import yaml
from loguru import logger


class P013(object):
    """携程酒店数据抓取类"""

    BASE_URL = "https://m.ctrip.com/restapi/soa2/34951/fetchHotelList"
    HEADERS = {
        'content-type': 'application/json',
        'referer': 'https://hotels.ctrip.com/',
        'sec-ch-ua': '"Not-A.Brand";v="99", "Google Chrome";v="157", "Chromium";v="157"',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/157.0.0.0 Safari/537.36',
        'w-payload-source': '1.0.9@102!+XtSw6CnG64b+X4I9ENPOX9V+6jlK6KZGrT59EOaKPCaOEbRKXt2OPKbOrK2+ET5+rApbbbpOSVLOlGIKSV2KrtZbEkbKtb5+rbSKrbnKStp+EVpOlk/KSGpKkbpOSkSOrAZKEA5+EbSQl4RGrdItLIDFPC7z5b=',
    }
    COOKIES = {
        'UBT_VID': '1783517010803.28a8yCNnVaOk',
    }

    def __init__(self):
        """
        初始化方法
        """
        self.headers = self.HEADERS
        self.cookies = self.COOKIES
        filename = os.path.dirname(__file__)
        self.ctx = execjs.compile(self._load_JavaScript(filename))
        config = self._load_config(filename)
        self.pages = config["app"]["pages"]
        self.timeout = config["app"]["timeout"]
        self.checkIn = config["app"]["checkIn"]
        self.checkOut = config["app"]["checkOut"]
        self.checkInDate = config["app"]["checkInDate"]
        self.checkOutDate = config["app"]["checkOutDate"]

    @staticmethod
    def _deep_merge(base, override):
        """
        递归合并本地配置，覆盖同名键
        """
        result = dict(base)
        for key, value in override.items():
            if isinstance(value, dict) and isinstance(result.get(key), dict):
                result[key] = P013._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

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
                config = P013._deep_merge(config, yaml.safe_load(f) or {})
        return config

    @staticmethod
    def _load_JavaScript(filename):
        """
        加载JavaScript代码文件
        :param filename: JavaScript代码文件路径
        :return: JavaScript代码
        """
        filename = os.path.join(filename, 'P013.js')
        if not os.path.exists(filename):
            raise FileNotFoundError(f"JavaScript代码文件不存在：{filename}")
        with open(filename, 'r', encoding='utf-8') as f:
            return f.read()

    @staticmethod
    def _parse_data(response_json):
        """
        解析响应数据
        :param response_json: 接口返回的JSON数据
        :return: 酒店列表
        """
        data = response_json.get("data") or response_json
        hotelList = data.get("hotelList") or []
        hotel_list = []
        for hotel in hotelList:
            hotel_info = hotel.get("hotelInfo") or {}
            name_info = hotel_info.get("nameInfo") or {}
            comment_info = hotel_info.get("commentInfo") or {}
            position_info = hotel_info.get("positionInfo") or {}
            star_info = hotel_info.get("hotelStar") or {}
            advertise_info = hotel_info.get("advertiseInfo") or {}
            images = hotel_info.get("hotelImages", {}).get("multiImgs") or []
            coordinates = position_info.get("mapCoordinate") or [{}]
            rooms = []
            for room in hotel.get("roomInfo") or []:
                room_summary = room.get("summary") or {}
                bed_info = room.get("bedInfo") or {}
                room_tags = room.get("roomTags") or {}
                rooms.append({
                    "roomId": room_summary.get("roomId"),
                    "roomName": room_summary.get("saleRoomName"),
                    "bed": "、".join(bed_info.get("contentList") or []),
                    "advantageTags": [tag.get("tagTitle") for tag in room_tags.get("advantageTags") or []],
                    "encourageTags": [tag.get("tagTitle") for tag in room_tags.get("encourageTags") or []],
                })
            hotelId = hotel_info.get("summary", {}).get("hotelId")
            name = name_info.get("name")
            enName = name_info.get("enName")
            star = star_info.get("star")
            starType = star_info.get("starType")
            commentScore = comment_info.get("commentScore")
            commentDescription = comment_info.get("commentDescription")
            commenterNumber = comment_info.get("commenterNumber")
            recommendTags = [item.get("tagTitle") for item in comment_info.get("oneSentenceComment") or []]
            positionDesc = position_info.get("positionDesc")
            address = position_info.get("address")
            zoneNames = position_info.get("zoneNames") or []
            latitude = coordinates[0].get("latitude")
            longitude = coordinates[0].get("longitude")
            isAdHotel = advertise_info.get("isAdHotel")
            imageUrl = images[0].get("url") if images else ""
            hotel_list.append({
                "hotelId": hotelId,
                "name": name,
                "enName": enName or "",
                "star": star or "",
                "starType": starType or "",
                "commentScore": commentScore or "",
                "commentDescription": commentDescription or "",
                "commenterNumber": commenterNumber or "",
                "recommendTags": recommendTags,
                "positionDesc": positionDesc or "",
                "address": address or "",
                "zoneNames": zoneNames,
                "latitude": latitude or "",
                "longitude": longitude or "",
                "isAdHotel": isAdHotel or "",
                "imageUrl": imageUrl,
                "rooms": rooms,
            })
            logger.info(
                f"hotelId: {hotelId} | name: {name} | enName: {enName} | star: {star} | starType: {starType} | commentScore: {commentScore} | commentDescription: {commentDescription} | commenterNumber: {commenterNumber} | recommendTags: {recommendTags} | positionDesc: {positionDesc} | address: {address} | zoneNames: {zoneNames} | latitude: {latitude} | longitude: {longitude} | isAdHotel: {isAdHotel} | imageUrl: {imageUrl}")
        return hotel_list

    def _fetch_data(self, page):
        """
        发送网络请求，获取响应数据
        :param page:
        :return:
        """
        json_data = {
            'date': {
                'dateType': 1,
                'dateInfo': {
                    'checkInDate': self.checkInDate,
                    'checkOutDate': self.checkOutDate,
                },
            },
            'extension': [
                {
                    'name': 'EnableProductId',
                    'value': 'T',
                },
            ],
            'destination': {
                'type': 1,
                'geo': {
                    'cityId': 2,
                    'countryId': 1,
                },
                'keyword': {
                    'word': '',
                },
            },
            'extraFilter': {
                'childInfoItems': [],
                'ctripMainLandBDCoordinate': True,
                'sessionId': '1a5fd58c9552436d9600a6954e32b366',
                'extendableParams': {
                    'tripWalkDriveSwitch': 'T',
                },
            },
            'filters': [
                {
                    'type': '17',
                    'title': '欢迎度排序',
                    'value': '1',
                    'filterId': '17|1',
                },
                {
                    'type': '80',
                    'title': '',
                    'value': '2',
                    'filterId': '80|2',
                },
                {
                    'filterId': '29|1',
                    'type': '29',
                    'value': '1|1',
                },
            ],
            'roomQuantity': 1,
            'marketInfo': {},
            'paging': {
                'pageIndex': page,
                'pageSize': 10,
                'pageCode': '10650171192',
            },
            'hotelIdFilter': {
                'hotelAldyShown': [],
            },
            'head': {
                'platform': 'PC',
                'cver': '0',
                'cid': '1783517010803.28a8yCNnVaOk',
                'bu': 'HBU',
                'group': 'ctrip',
                'aid': '',
                'sid': '',
                'ouid': '',
                'locale': 'zh-CN',
                'timezone': '8',
                'currency': 'CNY',
                'pageId': '10650171192',
                'vid': '1783517010803.28a8yCNnVaOk',
                'guid': '',
                'isSSR': False,
                'extension': [
                    {
                        'name': 'cityId',
                        'value': '2',
                    },
                    {
                        'name': 'checkIn',
                        'value': self.checkIn,
                    },
                    {
                        'name': 'checkOut',
                        'value': self.checkOut,
                    },
                    {
                        'name': 'region',
                        'value': 'CN',
                    },
                ],
            },
        }
        phantom_token = self.ctx.call('get_phantom_token', json_data)
        self.headers['phantom-token'] = phantom_token
        response = requests.post(self.BASE_URL, cookies=self.cookies, headers=self.headers, json=json_data)
        if response.status_code == 200:
            return response.json()
        else:
            raise Exception(f"请求失败，状态码：{response.status_code}")

    def run(self):
        """
        主方法入口
        """
        for page in range(1, self.pages + 1):
            response_json = self._fetch_data(page)
            hotel_list = self._parse_data(response_json)
            logger.info(f"第 {page} 页数据采集完成，共解析酒店 {len(hotel_list)} 家" + "\n")


if __name__ == '__main__':
    p013 = P013()
    p013.run()
