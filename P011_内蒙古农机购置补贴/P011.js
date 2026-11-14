const sm4 = require('sm-crypto').sm4;
const sm3 = require('sm-crypto').sm3;

function h(t) {
    var e = JSON.parse(t)
        , n = Object.keys(e).sort()
        , a = n.map((function (t) {
            var n = e[t];
            if (n) {
                var a = ""
                    , o = encodeURIComponent(t);
                return a = "object" === typeof n ? JSON.stringify(n) : n,
                    "".concat(o, "=").concat(a)
            }
        }
    ));
    a = a.filter((function (t) {
            return void 0 !== t && null !== t && "" !== t
        }
    ));
    var o = a.join("&");
    return o
}

function f(t, key) {
    var data = JSON.parse(sm4.decrypt(t.parameter, key));
    data.timestamp = Date.now();
    var str = JSON.stringify(data);
    var e = h(str) + "&key=HD7232D2AAAKA@978D8723H211?IER&6";
    return {
        sign: sm4.encrypt(sm3(e).toLocaleUpperCase(), key),
        timestamp: sm4.encrypt(data.timestamp.toString(), key),
        source: "ZRCSL7V0JIRK1PHY"
    };
}

function encrypt_data(data) {
    const key = "30062AFC48C0E7B5B0918851C0445A37";
    data = JSON.stringify(data);
    let parameter = sm4.encrypt(data, key);
    let enc_data = {"parameter": parameter}
    let headers_dict = f(enc_data, key)
    return {
        "headers": headers_dict,
        "body": enc_data
    }
}

function decrypt_data(data) {
    let enc_data = data["data"]
    return sm4.decrypt(enc_data, "30062AFC48C0E7B5B0918851C0445A37")
}

