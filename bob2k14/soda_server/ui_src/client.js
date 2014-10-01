/// <reference path="../typings/tsd.d.ts"/>
(function (ClientType) {
    ClientType[ClientType["Terminal"] = 0] = "Terminal";
    ClientType[ClientType["Soda"] = 1] = "Soda";
})(exports.ClientType || (exports.ClientType = {}));
var ClientType = exports.ClientType;

var Client = (function () {
    function Client(type, id) {
    }
    return Client;
})();
exports.Client = Client;
