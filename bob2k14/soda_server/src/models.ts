/// <reference path="../typings/tsd.d.ts"/>

var sequelize = require("sequelize");

export interface SequelizeModel {
    findAll();
    find();
}

export class Models {
    sql;

    Transactions: SequelizeModel;
    Products: SequelizeModel;
    Users: SequelizeModel;

    constructor (sql) {
        this.sql = sql;

        this.Products = sql.define('products', {
            barcode: { type: sequelize.STRING, primaryKey: true },
            name: sequelize.STRING,
            phonetic_name: sequelize.STRING,
            price: sequelize.DECIMAL,
            bulkid: sequelize.INTEGER,
            coffee: sequelize.BOOLEAN
        }, {timestamps : false});

        this.Users = sql.define('users', {
            userid: { type: sequelize.INTEGER, primaryKey: true},
            username: sequelize.STRING,
            email: sequelize.STRING,
            nickname: sequelize.STRING,
            pwd: sequelize.STRING,
            balance: sequelize.DECIMAL,
            disabled: sequelize.BOOLEAN,
            last_purchase_time: sequelize.DATE,
            last_deposit_time: sequelize.DATE,
            pref_auto_logout: sequelize.BOOLEAN,
            pref_speech: sequelize.BOOLEAN,
            pref_forget_which_product: sequelize.BOOLEAN,
            pref_skip_purchase_confirm: sequelize.BOOLEAN,
            notes: sequelize.STRING,
            created_time: sequelize.DATE,
            fraudulent: sequelize.BOOLEAN
        }, {timestamps: false});

        this.Transactions = sql.define('transactions', {
            xacttime : sequelize.DATE,
            userid : sequelize.INTEGER,
            xactvalue: sequelize.STRING,
            xacttype: sequelize.STRING,
            barcode: sequelize.STRING,
            source: sequelize.STRING,
            id: { type: sequelize.INTEGER, primaryKey: true},
            finance_trans_id: sequelize.INTEGER
        })
    }
}
