/// <reference path="../typings/tsd.d.ts"/>
/// <reference path="../typings/node/node.d.ts"/>
/// <reference path="../typings/jquery/jquery.d.ts"/>

import $ = require("jquery");

export enum ClientType {
    Terminal = 0,
    Soda = 1
}

export class Client
{

    constructor(type: ClientType, id: number) {

    }
}
