const CryptoJS = require('crypto-js')

var window = globalThis;


function q(LZ) {
    var LE = new URL(LZ);
    return {
        'protocol': LE['protocol'],
        'host': LE['host'],
        'hostname': LE['hostname'],
        'port': LE['port'],
        'pathname': LE['pathname'],
        'search': LE['search'],
        'hash': LE['hash'],
        'original': LE['href']
    };
}

function y(LZ) {
    var Le = CryptoJS.MD5(LZ).toString()
    return Le
}

function LS(LZ) {
    var LM = y(LZ)
    for (var Lj = [], LW = 5; LW < 21; ++LW)
        Lj['push'](LM[LW % LM['length']]);
    return Lj;
}

let L0 = function (LZ) {
    for (var LE = LZ['slice'](), Lb = LE['length'] - 1; Lb >= 0; Lb--) {
        var Lj = window['Math']['floor']((Math.random() * (Lb + 1)))
        var LW = LE[Lj];
        LE[Lj] = LE[Lb],
            LE[Lb] = LW;
    }
    return LE['length'], LE;
}

let H = function (LZ, LE) {
    var Ld = {};
    Ld['eIrUs'] = 'function random() { [native code] }';
    var LB = Ld;

    var p = 1691596516;
    var Lc = 1436544;
    var LW = 3074446023
    var LM = function () {
        p = (((Lc * p) + LZ) % LW)
        return p / LW;
    };
    return LM['toString'] = function () {
        return LB['eIrUs'];
    }, LM;
};

function Li(LZ) {
    return LZ = L0(LZ), LZ['join']('')['toLowerCase']();
}

function u(zz, zh) {
    const k = "WupoePhf73Q6wvF1jtJY9ig8bTk0zNmnEAlBR5VxU=crCyqaLDdGXM/2O_s4SKIZH"
    return function (zj, zU, zB) {
        var zL, zI, zv, zu = {}, zX = {}, zK = '', zc = '', zE = '',
            zq = 2, zy = 3,
            zJ = 2, zS = [], zW = 0,
            ze = 0;
        for (zv = 0; (zv < zj['length']); zv += 1)
            if (zK = zj['charAt'](zv),
            Object['prototype']['hasOwnProperty']['call'](zu, zK) || (zu[zK] = zy,
                zy += 1,
                zX[zK] = !(0)),
                zc = (zE + zK),
                Object['prototype']['hasOwnProperty']['call'](zu, zc))
                zE = zc;
            else {
                if (Object['prototype']['hasOwnProperty']['call'](zX, zE)) {
                    if ((zE['charCodeAt'](0) < 256)) {
                        for (zL = 0; (zL < zJ); zL++)
                            zW <<= 1,
                                (ze == (zU - 1)) ? (ze = 0,
                                    zS['push'](zB(zW)),
                                    zW = 0) : ze++;
                        for (zI = zE['charCodeAt'](0),
                                 zL = 0; (zL < 8); zL++)
                            zW = ((zW << 1) | (1 & zI)),
                                (ze == (zU - 1)) ? (ze = 0,
                                    zS['push'](zB(zW)),
                                    zW = 0) : ze++,
                                zI >>= 1;
                    } else {
                        for (zI = 1,
                                 zL = 0; (zL < zJ); zL++)
                            zW = ((zW << 1) | zI),
                                (ze == (zU - 1)) ? (ze = 0,
                                    zS['push'](zB(zW)),
                                    zW = 0) : ze++,
                                zI = 0;
                        for (zI = zE['charCodeAt'](0),
                                 zL = 0; (zL < 16); zL++)
                            zW = ((zW << 1) | (1 & zI)),
                                (ze == (zU - 1)) ? (ze = 0,
                                    zS['push'](zB(zW)),
                                    zW = 0) : ze++,
                                zI >>= 1;
                    }
                    (0 == --zq) && (zq = Math['pow'](2, zJ),
                        zJ++),
                        delete zX[zE];
                } else {
                    for (zI = zu[zE],
                             zL = 0; (zL < zJ); zL++)
                        zW = ((zW << 1) | (1 & zI)),
                            (ze == (zU - 1)) ? (ze = 0,
                                zS['push'](zB(zW)),
                                zW = 0) : ze++,
                            zI >>= 1;
                }
                (0 == --zq) && (zq = Math['pow'](2, zJ),
                    zJ++),
                    zu[zc] = zy,
                    zy += 1,
                    zE = String(zK);
            }
        if (('' !== zE)) {
            if (Object['prototype']['hasOwnProperty']['call'](zX, zE)) {
                if ((zE['charCodeAt'](0) < 256)) {
                    for (zL = 0; (zL < zJ); zL++)
                        zW <<= 1,
                            (ze == (zU - 1)) ? (ze = 0,
                                zS['push'](zB(zW)),
                                zW = 0) : ze++;
                    for (zI = zE['charCodeAt'](0),
                             zL = 0; (zL < 8); zL++)
                        zW = ((zW << 1) | (1 & zI)),
                            (ze == (zU - 1)) ? (ze = 0,
                                zS['push'](zB(zW)),
                                zW = 0) : ze++,
                            zI >>= 1;
                } else {
                    for (zI = 1,
                             zL = 0; (zL < zJ); zL++)
                        zW = ((zW << 1) | zI),
                            (ze == (zU - 1)) ? (ze = 0,
                                zS['push'](zB(zW)),
                                zW = 0) : ze++,
                            zI = 0;
                    for (zI = zE['charCodeAt'](0),
                             zL = 0; (zL < 16); zL++)
                        zW = ((zW << 1) | (1 & zI)),
                            (ze == (zU - 1)) ? (ze = 0,
                                zS['push'](zB(zW)),
                                zW = 0) : ze++,
                            zI >>= 1;
                }
                (0 == --zq) && (zq = Math['pow'](2, zJ),
                    zJ++),
                    delete zX[zE];
            } else {
                for (zI = zu[zE],
                         zL = 0; (zL < zJ); zL++)
                    zW = ((zW << 1) | (1 & zI)),
                        (ze == (zU - 1)) ? (ze = 0,
                            zS['push'](zB(zW)),
                            zW = 0) : ze++,
                        zI >>= 1;
            }
            (0 == --zq) && (zq = Math['pow'](2, zJ),
                zJ++);
        }
        for (zI = 2,
                 zL = 0; (zL < zJ); zL++)
            zW = ((zW << 1) | (1 & zI)),
                (ze == (zU - 1)) ? (ze = 0,
                    zS['push'](zB(zW)),
                    zW = 0) : ze++,
                zI >>= 1;
        for (; ;) {
            if (zW <<= 1,
                (ze == (zU - 1))) {
                zS['push'](zB(zW));
                break;
            }
            ze++;
        }
        return zS['join']('');
    }(zz, 6, function (zj) {
        return k[zj];
    });
}

function LK(LZ, LE, Lb, renderData) {
    var Ls = window;
    Ls['_waf_bd8ce2ce37'] = renderData['_waf_bd8ce2ce37']
    Ls['_waf_a86dfdc5f2'] = renderData['_waf_a86dfdc5f2']
    Lb || (Lb = 'GET'), Lb = Lb['toLowerCase']();
    var LD = q(LZ)
    var LV = LD["host"] + LD["pathname"]
    var Lm = LV
    var LI = Lm = window['encodeURIComponent']((((Ls['_waf_bd8ce2ce37'] + Lb) + '2790552d') + Lm));
    Lm += window['encodeURIComponent'](LE);
    window['Math']['random'] = H(760093734);
    var LR = LS(Lm);
    var Lk = LR;
    (Lm != LI) && (Lk = LS(LI))
    LR = [Li(LR), Li(Lk), 67245056, (new window['Date']()['getTime']() + ''), Ls['_waf_bd8ce2ce37'], Ls['_waf_a86dfdc5f2'], '209888129a1a1a23407a6']['join']('|');
    var Lg = '2790552d-' + u(LR)
    return Lg
}


// LZ = "https://api-pc.pxb7.com/api/bff/web/product/search/productPage"
// LE = '{"query":"","gameId":"10013","pageIndex":4,"pageSize":16,"bizProd":1,"type":"4","posType":1,"filterDTOList":[],"combineFilterList":[],"pageToken":"TIdWSiXvxeAL4n7OdzUHN1jYFegTwJMRqj_7SxAKg2g"}'
// Lb = 'POST'
// Lj = 2
// console.log(LK(LZ, LE, Lb));