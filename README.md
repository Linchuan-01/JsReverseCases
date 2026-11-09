<div align="center">

# 🔐 JS 逆向案例集

**JS Reverse Engineering Cases**

Web 端加密参数逆向 · 实战案例库

</div>

---

## 📖 项目简介

本项目是一个 **JavaScript 逆向工程实战案例库**，收录了多个真实平台的加密参数分析与还原过程。

每个案例独立成目录，记录了从**接口定位 → 加密参数识别 → 算法还原 → 采集实现**的完整链路。案例之间互不依赖，可单独阅读与参考。

> **声明**：本项目仅供学习研究与技术交流使用，不得用于任何商业用途或非法用途。所有案例均针对公开可访问的接口进行分析，不涉及任何用户隐私数据采集。

---

## 🗂️ 案例索引

| 编号 | 平台名称 | 加密参数 | 防护类型 | 状态 |
|:---:|:---|:---|:---|:---:|
| P001 | 螃蟹账号交易平台 | `timestamp__1366` | 阿里云 WAF 动态签名 | ✅ |
| P002 | 盼之代售 | — | — | 📝 待补充 |
| P003 | 7881 账号交易平台 | `lb-sign` / `lb-timestamp` | MD5 哈希签名 | ✅ |

---

## 📂 目录结构

```
JS逆向项目/
│
├── P001_螃蟹账号交易平台/
│   ├── config.yaml        # 采集配置（数据库/Redis/应用参数）
│   ├── P001.js            # 加密算法 JS 实现（execjs 调用）
│   └── P001.py            # 采集主程序（签名生成 + 采集 + 入库去重）
│
├── P002_盼之代售/
│   └── (待补充)
│
└── P003_7881账号交易平台/
    ├── config.yaml        # 采集配置
    └── P003.py            # 采集主程序（MD5 签名生成 + 采集）
```

> 每个案例目录内的文件即该案例的全部产物，不涉及跨案例的公共依赖或共享配置。根目录 `package.json` 仅声明 `crypto-js` 依赖，供 P001 的 JS 算法执行使用。

---

## 📝 案例详解

### P001 — 螃蟹账号交易平台

<table>
<tr><td><b>目标页面</b></td><td><code>https://www.pxb7.com/buy/10013/1</code></td></tr>
<tr><td><b>数据接口</b></td><td><code>https://api-pc.pxb7.com/api/bff/web/product/search/productPage</code></td></tr>
<tr><td><b>加密参数</b></td><td>查询字符串 <code>timestamp__1366</code></td></tr>
<tr><td><b>防护类型</b></td><td>阿里云 WAF（动态令牌 + 请求签名）</td></tr>
<tr><td><b>涉及文件</b></td><td><code>P001.js</code>（算法）、<code>P001.py</code>（采集）</td></tr>
</table>

**算法流程：**

1. 首次请求获取动态令牌（`_waf_bd8ce2ce37`）与 `acw_tc` Cookie
2. 拼接签名材料：`WAF令牌 + 请求方法 + 盐值 + URL路径`
3. MD5 提取子串生成签名种子，LZ 字典压缩编码
4. 自定义随机数生成器（LCG）参与混淆
5. 最终输出格式：`2790552d-{压缩编码结果}`

**核心函数：** `P001.js` → `LK(url, body, method, renderData)`

---

### P003 — 7881 账号交易平台

<table>
<tr><td><b>目标页面</b></td><td><code>https://search.7881.com/A5776-100003-0-0-0.html</code></td></tr>
<tr><td><b>数据接口</b></td><td><code>https://gw.7881.com/goods-service-api/api/goods/list</code></td></tr>
<tr><td><b>加密参数</b></td><td>请求头 <code>lb-sign</code>、<code>lb-timestamp</code></td></tr>
<tr><td><b>防护类型</b></td><td>自定义 MD5 哈希签名</td></tr>
<tr><td><b>涉及文件</b></td><td><code>P003.py</code>（签名 + 采集）</td></tr>
</table>

**算法流程：**

1. 取固定密钥 `5c2c538a3937c6db2d04bce3d03bbe88bl` 反转
2. 拼接当前毫秒级时间戳 `lb-timestamp`
3. 对拼接串做 MD5 得到中间密钥 `pubKey`
4. 将 `pubKey + 请求体JSON` 再做一次 MD5 得到 `lb-sign`

**核心函数：** `P003.py` → `_generate_Signature(paramObj)`

---

## ⚠️ 免责声明

```
本项目仅供技术学习与研究交流，不提供任何形式的担保。

· 所有案例均针对公开接口进行分析，不涉及用户隐私数据
· 请勿将本项目代码用于商业用途或任何违法违规行为
· 使用者需自行承担因不当使用产生的一切法律责任
· 项目作者不对任何因使用本代码造成的后果负责

请在遵守目标网站 robots.txt 及相关法律法规的前提下使用。
```

---

## 📄 License

本项目采用 [MIT License](LICENSE) 开源协议。
