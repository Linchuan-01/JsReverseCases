metaContent = "{meta_content}"
// <------------------------------------------删除浏览器不存在的属性------------------------------------------>
delete __filename;
delete __dirname;

// <------------------------------------------EventTarget对象------------------------------------------>
EventTarget = function EventTarget() {
};
EventTarget.prototype.toString = function toString() {
    return 'function EventTarget() { [native code] }'
};
EventTarget.prototype.toString.call = function toString() {
    return '[object Function]'
};
EventTarget.prototype.addEventListener = function addEventListener() {
};
Object.setPrototypeOf(EventTarget.prototype, globalThis);

// <------------------------------------------Node对象------------------------------------------>
Node = function Node() {
};
Node.prototype.toString = function toString() {
    return 'function Node() { [native code] }'
};
Node.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(Node.prototype, EventTarget.prototype)

// <------------------------------------------Element对象------------------------------------------>
Element = function Element() {
};
Element.prototype.toString = function toString() {
    return 'function Node() { [native code] }'
};
Element.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(Element.prototype, Node.prototype);

HTMLElement = function HTMLElement() {
}
HTMLElement.prototype.toString = function toString() {
    return 'function Node() { [native code] }'
};
HTMLElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLElement.prototype, Element.prototype)

// <------------------------------------------Window对象------------------------------------------>
Window = function Window() {
}
Window.prototype.toString = function toString() {
    return 'function Window() { [native code] }'
};
Window.prototype.toString.call = function toString() {
    return '[object Function]'
};
Window.prototype.constructor = Window;
Object.setPrototypeOf(Window.prototype, EventTarget.prototype)
window = Object.create(Window.prototype);
window.toString = function toString() {
    return '[object Window]'
};
window.toString.call = function toString() {
    return '[object Window]'
};
window.top = window.self = window.window = window;
window.attachEvent = function attachEvent() {
}
window.addEventListener = function addEventListener() {
}
window.setInterval = function setInterval() {
}
window.setTimeout = function setTimeout() {
}
window.ActiveXObject = undefined

// <------------------------------------------标签对象------------------------------------------>
HTMLDivElement = function HTMLDivElement() {
    this.tagName = "DIV"
};
HTMLDivElement.prototype.toString = function toString() {
    return 'function HTMLDivElement() { [native code] }'
};
HTMLDivElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
HTMLDivElement.prototype.getElementsByTagName = function getElementsByTagName(tagName) {
    if (tagName === "i") {
        return []
    }
};
Object.setPrototypeOf(HTMLDivElement.prototype, HTMLElement.prototype);
div = Object.create(HTMLDivElement.prototype);

HTMLBaseElement = function HTMLBaseElement() {
    this.tagName = "BASE"
    this.length = 0
};
HTMLBaseElement.prototype.toString = function toString() {
    return 'function HTMLBaseElement() { [native code] }'
};
HTMLBaseElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLBaseElement.prototype, HTMLElement.prototype);
base = Object.create(HTMLBaseElement.prototype);

HTMLScriptElement = function HTMLScriptElement() {
    this.tagName = "SCRIPT"
};
HTMLScriptElement.prototype.toString = function toString() {
    return 'function HTMLScriptElement() { [native code] }'
};
HTMLScriptElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
HTMLScriptElement.prototype.getAttribute = function getAttribute(tagName) {
    if (tagName === "r") {
        return "m"
    }
};
HTMLScriptElement.prototype.parentElement = {
    removeChild: function (args) {
    }
};
HTMLScriptElement.prototype.innerText = "";
Object.setPrototypeOf(HTMLScriptElement.prototype, HTMLElement.prototype);
script = Object.create(HTMLScriptElement.prototype);

HTMLAnchorElement = function HTMLAnchorElement() {
    this.tagName = "A"
};
HTMLAnchorElement.prototype.toString = function toString() {
    return 'function HTMLAnchorElement() { [native code] }'
};
HTMLAnchorElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLAnchorElement.prototype, HTMLElement.prototype);
a = Object.create(HTMLAnchorElement.prototype);

HTMLIFrameElement = function HTMLIFrameElement() {
    this.tagName = "IFRAME"
};
HTMLIFrameElement.prototype.toString = function toString() {
    return 'function HTMLIFrameElement() { [native code] }'
};
HTMLIFrameElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLIFrameElement.prototype, HTMLElement.prototype);
iframe = Object.create(HTMLIFrameElement.prototype);

HTMLImageElement = function HTMLImageElement() {
    this.tagName = "IMG"
};
HTMLImageElement.prototype.toString = function toString() {
    return 'function HTMLImageElement() { [native code] }'
};
HTMLImageElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLImageElement.prototype, HTMLElement.prototype);
img = Object.create(HTMLImageElement.prototype);

HTMLFormElement = function HTMLFormElement() {
    this.tagName = "FORM"
};
HTMLFormElement.prototype.toString = function toString() {
    return 'function HTMLFormElement() { [native code] }'
};
HTMLFormElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLFormElement.prototype, HTMLElement.prototype);
form = Object.create(HTMLFormElement.prototype);

HTMLInputElement = function HTMLInputElement() {
    this.tagName = "INPUT"
};
HTMLInputElement.prototype.toString = function toString() {
    return 'function HTMLInputElement() { [native code] }'
};
HTMLInputElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLInputElement.prototype, HTMLElement.prototype);
input = Object.create(HTMLInputElement.prototype);

HTMLCanvasElement = function HTMLCanvasElement() {
    this.tagName = "CANVAS"
};
HTMLCanvasElement.prototype.toString = function toString() {
    return 'function HTMLCanvasElement() { [native code] }'
};
HTMLCanvasElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
Object.setPrototypeOf(HTMLCanvasElement.prototype, HTMLElement.prototype);
canvas = Object.create(HTMLCanvasElement.prototype);
window.HTMLCanvasElement = HTMLCanvasElement;

CanvasRenderingContext2D = function CanvasRenderingContext2D() {
};
CanvasRenderingContext2D.prototype.toString = function toString() {
    return 'function CanvasRenderingContext2D() { [native code] }'
};
CanvasRenderingContext2D.prototype.toString.call = function toString() {
    return '[object Function]'
};
CanvasRenderingContext2D.prototype.constructor = CanvasRenderingContext2D;
Object.setPrototypeOf(CanvasRenderingContext2D.prototype, EventTarget.prototype)

canvas.getContext = function getContext(tagName) {
    if (tagName === "2d")
        return new CanvasRenderingContext2D()
}
window.CanvasRenderingContext2D = CanvasRenderingContext2D;

HTMLMetaElement = function HTMLMetaElement() {
    this.tagName = "META"
};
HTMLMetaElement.prototype.toString = function toString() {
    return 'function HTMLMetaElement() { [native code] }'
};
HTMLMetaElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
HTMLMetaElement.prototype.getAttribute = function getAttribute(tagName) {
    if (tagName === "r") {
        return "m"
    }
};
HTMLMetaElement.prototype.parentNode = {
    removeChild: function (args) {
    }
};
HTMLMetaElement.prototype.content = metaContent;
Object.setPrototypeOf(HTMLMetaElement.prototype, HTMLElement.prototype);
meta = Object.create(HTMLMetaElement.prototype);

HTMLBodyElement = function HTMLBodyElement() {
    this.tagName = "BODY"
};
HTMLBodyElement.prototype.toString = function toString() {
    return 'function HTMLBodyElement() { [native code] }'
};
HTMLBodyElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
HTMLBodyElement.prototype.getElementsByTagName = function getElementsByTagName(tagName) {
};
Object.setPrototypeOf(HTMLBodyElement.prototype, HTMLElement.prototype);
body = Object.create(HTMLBodyElement.prototype);

HTMLHtmlElement = function HTMLHtmlElement() {
    this.tagName = "HTML"
};
HTMLHtmlElement.prototype.toString = function toString() {
    return 'function HTMLHtmlElement() { [native code] }'
};
HTMLHtmlElement.prototype.toString.call = function toString() {
    return '[object Function]'
};
HTMLHtmlElement.prototype.getElementsByTagName = function getElementsByTagName(tagName) {
};
Object.setPrototypeOf(HTMLHtmlElement.prototype, HTMLElement.prototype);
documentElement = Object.create(HTMLHtmlElement.prototype);
// <------------------------------------------Document对象------------------------------------------>
Document = function Document() {
};
Document.prototype.toString = function toString() {
    return 'function Document() { [native code] }'
};
Document.prototype.toString.call = function toString() {
    return '[object Function]'
}
Document.prototype.getElementsByTagName = function getElementsByTagName(tagName) {
    if (tagName === "base") {
        return base
    } else if (tagName === "script") {
        return [script, script, script]
    } else if (tagName === "meta") {
        return [meta, meta]
    }
};
Document.prototype.createElement = function createElement(tagName) {
    if (tagName === "div") {
        return div
    }
    if (tagName === "form") {
        return form
    }
    if (tagName === "a") {
        return a
    }
};
Document.prototype.getElementById = function getElementById(tagName) {
    if (tagName === "body") {
        return body
    }
};
Document.prototype.appendChild = function appendChild(args) {
};
Document.prototype.removeChild = function removeChild(args) {
}
Document.prototype.constructor = Document;
Object.setPrototypeOf(Document.prototype, Node.prototype)
HTMLDocument = function HTMLDocument() {
};
HTMLDocument.prototype.toString = function toString() {
    return 'function HTMLDocument() { [native code] }'
};
HTMLDocument.prototype.toString.call = function toString() {
    return '[object Function]'
}
HTMLDocument.prototype.visibilityState = "visible";
HTMLDocument.prototype.characterSet = "UTF-8";
HTMLDocument.prototype.charset = "UTF-8";
HTMLDocument.prototype.body = body;
HTMLDocument.prototype.documentElement = documentElement;
Object.setPrototypeOf(HTMLDocument.prototype, Document.prototype)
document = Object.create(HTMLDocument.prototype);
window.document = document;

// <------------------------------------------history对象------------------------------------------>
History = {};
History.prototype = Object.create(Object.prototype);
history = Object.create(History.prototype);
window.history = history;

// <------------------------------------------screen对象------------------------------------------>
Screen = {};
Screen.prototype = Object.create(Object.prototype);
screen = Object.create(Screen.prototype);
screen.width = 1920;
screen.height = 1080;
screen.availWidth = 1920;
screen.availHeight = 1040;
window.screen = screen;

// <------------------------------------------location对象------------------------------------------>
Location = function Location() {
};
Location.prototype.toString = function toString() {
    return 'function Location() { [native code] }'
};
Location.prototype.toString.call = function toString() {
    return '[object Function]'
};
location = {
    "ancestorOrigins": {},
    "href": "https://zhaopin.sgcc.com.cn/sgcchr/static/recrAument.html",
    "origin": "https://zhaopin.sgcc.com.cn",
    "protocol": "https:",
    "host": "zhaopin.sgcc.com.cn",
    "hostname": "zhaopin.sgcc.com.cn",
    "port": "",
    "pathname": "$pathname$",
    "search": "",
    "hash": ""
};
Object.assign(Location.prototype, location)
window.location = location;

// <------------------------------------------navigator对象------------------------------------------>
Navigator = function Navigator() {
};
Navigator.prototype.toString = function toString() {
    return 'function Navigator() { [native code] }'
};
Navigator.prototype.toString.call = function toString() {
    return '[object Function]'
};
navigator = {
    "appCodeName": "Mozilla",
    "appName": "Netscape",
    "appVersion": "{app_version}",
    "platform": "Win32",
    "userAgent": "{user_agent}",
    "language": "zh-CN",
    "languages": ["zh-CN", "zh", "en-US", "en"],
    "webdriver": false,
}
Object.assign(Navigator.prototype, navigator)
window.navigator = navigator;

// <------------------------------------------XMLHttpRequest对象------------------------------------------>
let req_params;
XMLHttpRequest = function XMLHttpRequest() {
};
XMLHttpRequest.prototype.toString = function toString() {
    return 'function XMLHttpRequest() { [native code] }'
};
XMLHttpRequest.prototype.toString.call = function toString() {
    return '[object Function]'
};
XMLHttpRequest.prototype.open = function open(method, url) {
    req_params = url;
    return url
};
XMLHttpRequest.prototype.send = function send() {
};
window.XMLHttpRequest = XMLHttpRequest;

// <------------------------------------------核心代码------------------------------------------>

{ts_code}
{dynamic_script}
// require("./code")



//<------------------------------------------获取cookies------------------------------------------>
get_cookies = function get_cookies() {
    let cookies = document.cookie.split(";")[0].split("=")
    let key = cookies[0]
    let value = cookies[1]
    return {
        [key]: value
    }
}
// console.log(getCookies())

// <------------------------------------------获取后缀------------------------------------------>
a_synchronize = function a_synchronize(_url) {
    const urls = new URL(_url);
    const pathname = urls.pathname;
    const search = urls.search;
    const path = pathname + search;
    a.href = _url;
    a.pathname = pathname;
    a.search = search;
    a.host = urls.host;
    a.hostname = urls.hostname;
    a.protocol = urls.protocol;
    a.port = urls.port;
    a.origin = urls.origin;
    a.hash = urls.hash;
    return path
}


getSuffix = function getSuffix(_url) {
    const path = a_synchronize(_url)
    const g = new XMLHttpRequest()
    g.open("GET", path, true);
    return req_params.split("\n")[0]
}
// console.log(getSuffix("https://public.creditchina.gov.cn/private-api/catalogSearch?keyword=&scenes=scenario1&tableName=credit_xyzg_zxzltx_sxbzxr_xzcf&searchState=2&page=1&pageSize=10"));