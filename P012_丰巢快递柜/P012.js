const CryptoJS = require('crypto-js');
const {JSEncrypt} = require('node-jsencrypt')


function H5uuid() {
    for (var _0x3e800f = [], _0x48358b = '0123456789abcdef', _0x967e70 = 0x0; _0x967e70 < 0x24; _0x967e70++)
        _0x3e800f[_0x967e70] = _0x48358b['substr'](Math['floor'](0x10 * Math['random']()), 0x1);
    return _0x3e800f[0xe] = '4',
        _0x3e800f[0x13] = _0x48358b['substr'](0x3 & _0x3e800f[0x13] | 0x8, 0x1),
        _0x3e800f[0x8] = _0x3e800f[0xd] = _0x3e800f[0x12] = _0x3e800f[0x17] = '-',
        _0x3e800f['join']('');
}

function _0x44bc33(_0x5dc092) {
    for (var _0x375f61 = '', _0x175ca2 = 0x0; _0x175ca2 < _0x5dc092['length']; _0x175ca2++) {
        var _0xa32b9a = _0x5dc092[_0x175ca2];
        _0x375f61 += _0xa32b9a['x'] + '' + _0xa32b9a['y'] + _0xa32b9a['time'];
    }
    return _0x375f61;
}

function _0x58a573(_0x5a6b8f) {
    return CryptoJS.MD5(_0x5a6b8f).toString()
}
function _0x5b9645(_0x2033bb) {
    var _0x205dfc = _0x2033bb['data']
    var _0x4b7c09 = CryptoJS.enc.Utf8['parse'](_0x2033bb['aesKey'])
    var _0x1e3366 = JSON['stringify'](_0x205dfc)
    var _0xf16402 = CryptoJS.enc.Utf8['parse'](_0x1e3366);
    return CryptoJS.AES['encrypt'](_0xf16402, _0x4b7c09, {
        'mode': CryptoJS.mode.ECB,
        'padding': CryptoJS.pad.Pkcs7
    })['toString']();
}
function EncryptData(clientIp, checkId, H5uuid, tracks, aesKey) {
    let _0x5a6b8f = clientIp + checkId + H5uuid + _0x44bc33(tracks)
    let _0x427682 = _0x58a573(_0x5a6b8f)
    let _0xa5e81f = _0x5b9645({
        'data': {
            'sign': _0x427682,
            'track': tracks
        },
        'aesKey': aesKey
    })
    return _0xa5e81f
}


function EncryptPWD(pwd, public_key){
    let encrypt = new JSEncrypt()
    encrypt.setPublicKey(public_key)
    return encrypt.encrypt(pwd)
}

// clientIp = "103.231.14.69"
// checkId = "04F3B3D624B048FB8E5D7BD65BA4225B"
// H5uuid = "ab61aa00-2d14-45bf-87b7-63f5a1519c5d"
// aesKey = "Z17SGBjqKALe8NOp"
// tracks = [
//     {
//         "x": 1,
//         "y": 55,
//         "time": 1794635940058
//     },
//     {
//         "x": 1,
//         "y": 55,
//         "time": 1794635940070
//     },
//     {
//         "x": 3,
//         "y": 55,
//         "time": 1794635940077
//     },
//     {
//         "x": 8,
//         "y": 55,
//         "time": 1794635940085
//     },
//     {
//         "x": 12,
//         "y": 55,
//         "time": 1794635940092
//     },
//     {
//         "x": 17,
//         "y": 55,
//         "time": 1794635940107
//     },
//     {
//         "x": 25,
//         "y": 55,
//         "time": 1794635940115
//     },
//     {
//         "x": 36,
//         "y": 55,
//         "time": 1794635940122
//     },
//     {
//         "x": 55,
//         "y": 55,
//         "time": 1794635940130
//     },
//     {
//         "x": 74,
//         "y": 55,
//         "time": 1794635940137
//     },
//     {
//         "x": 101,
//         "y": 55,
//         "time": 1794635940145
//     },
//     {
//         "x": 127,
//         "y": 55,
//         "time": 1794635940152
//     },
//     {
//         "x": 151,
//         "y": 55,
//         "time": 1794635940160
//     },
//     {
//         "x": 175,
//         "y": 55,
//         "time": 1794635940167
//     },
//     {
//         "x": 194,
//         "y": 55,
//         "time": 1794635940175
//     },
//     {
//         "x": 205,
//         "y": 55,
//         "time": 1794635940182
//     },
//     {
//         "x": 207,
//         "y": 55,
//         "time": 1794635940191
//     }
// ]

// console.log(EncryptData(clientIp, checkId, H5uuid, tracks, aesKey));

