/// <reference path="../typings/tsd.d.ts"/>

var sequelize = require("sequelize");

export interface SequelizeModel {
    findAndCountAll();
    findAll();
    find();
    create();
    hasOne(model: SequelizeModel, opts?:any);
}

export class Models {
    sql;

    Fingerprints : SequelizeModel;

    constructor (sql, type) {
        var dateFn;

        if (type == "postgres")
          dateFn = "NOW";
        else
          dateFn = "date";

        this.sql = sql;

        this.Fingerprints = sql.define('fingerprints', {
            userid: { type: sequelize.INTEGER, primaryKey: true},
            fpdata: sequelize.BLOB,
            fpimg: sequelize.BLOB,
        }, {timestamps: false});
    }
}
