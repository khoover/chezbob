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

    //AggregatePurchases: SequelizeModel;
    BulkItems: SequelizeModel;
    FinanceAccounts: SequelizeModel;
    FinanceDepositSummary: SequelizeModel;
    FinanceInventorySummary: SequelizeModel;
    FinanceSpits: SequelizeModel;
    FinanceTransactions: SequelizeModel;
    FloorLocations: SequelizeModel;
    HistoricalPrices: SequelizeModel;
    //Inventory: SequelizeModel;
    Messages: SequelizeModel;
    OrderItems: SequelizeModel;
    Orders: SequelizeModel;
    ProductSoure: SequelizeModel;
    Products: SequelizeModel;
    DynamicProducts: SequelizeModel;
    //Profiles: SequelizeModel;
    Roles: SequelizeModel;
    SodaInventory: SequelizeModel;
    Transactions: SequelizeModel;
    //UcsdEmails: SequelizeModel;
    Userbarcodes: SequelizeModel;
    Users: SequelizeModel;

    constructor (sql, type) {
        var dateFn;

        if (type == "postgres")
          dateFn = "NOW";
        else
          dateFn = "date";

        this.sql = sql;

        this.BulkItems = sql.define('bulk_items', {
            bulkid: { type: sequelize.INTEGER, primaryKey: true },
            description: sequelize.STRING,
            price: sequelize.DECIMAL,
            taxable: sequelize.BOOLEAN,
            quantity: sequelize.INTEGER,
            updated: sequelize.DATE,
            crv: sequelize.DECIMAL,
            crv_taxable: sequelize.BOOLEAN,
            source: sequelize.INTEGER,
            reserve: sequelize.INTEGER,
            active: sequelize.BOOLEAN,
            floor_location: sequelize.INTEGER,
            product_id: sequelize.STRING,
            crv_per_unit: sequelize.INTEGER,
        }, {timestamps : false});

        this.FinanceAccounts = sql.define('finance_accounts', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            type: sequelize.STRING,
            name: sequelize.STRING,
        }, {timestamps : false});

        this.FinanceDepositSummary = sql.define('finance_deposit_summary', {
            date: { type: sequelize.DATE, primaryKey: true },
            positive: sequelize.DECIMAL,
            negative: sequelize.DECIMAL,
        }, {timestamps : false});

        this.FinanceInventorySummary = sql.define('finance_inventory_summary', {
            date: { type: sequelize.DATE, primaryKey: true },
            value: sequelize.DECIMAL,
            shrinkage: sequelize.DECIMAL,
        }, {timestamps : false});

        this.FinanceSpits = sql.define('finance_splits', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            transaction_id: sequelize.INTEGER,
            account_id: sequelize.INTEGER,
            amount: sequelize.DECIMAL,
	    memo: sequelize.STRING
        }, {timestamps : false});

        this.FinanceTransactions = sql.define('finance_transactions', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            date: sequelize.DATE,
            description: sequelize.STRING,
            auto_generated: sequelize.BOOLEAN,
        }, {timestamps : false});

        this.FloorLocations = sql.define('floor_locations', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            name: sequelize.STRING,
            markup: sequelize.FLOAT,
        }, {timestamps : false});

        this.HistoricalPrices = sql.define('historical_prices', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            bulkid: sequelize.INTEGER,
            date: sequelize.DATE,
            price: sequelize.DECIMAL,
        }, {timestamps : false});

/* TODO: (dbounov) adding inventory is also problematic due to lack of a 
single column primary key
        this.Inventory = sql.define('inventory', {
        }, {timestamps : false});
*/
        this.Messages = sql.define('messages', {
            msgid: { type: sequelize.INTEGER, primaryKey: true },
            msgtime: sequelize.DATE,
            userid: sequelize.INTEGER,
            message: sequelize.STRING,
        }, {timestamps : false});

        this.OrderItems = sql.define('order_items', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            order_id: sequelize.INTEGER,
            bulk_type_id: sequelize.INTEGER,
            quantity: sequelize.INTEGER,
            number: sequelize.INTEGER,
            case_cost: sequelize.DECIMAL,
            crv_per_unit: sequelize.DECIMAL,
            is_cost_taxed: sequelize.BOOLEAN,
            is_crv_taxed: sequelize.BOOLEAN,
            is_cost_migrated: sequelize.BOOLEAN,
        }, {timestamps : false});

        this.Orders = sql.define('orders', {
            id: { type: sequelize.INTEGER, primaryKey: true },
            date: sequelize.DATE,
            description: sequelize.STRING,
            amount: sequelize.DECIMAL,
            tax_rate: sequelize.DECIMAL,
            inventory_adjust: sequelize.DECIMAL,
            supplies_adjust: sequelize.DECIMAL,
            supplies_taxed: sequelize.DECIMAL,
            supplies_nontaxed: sequelize.DECIMAL,
            finance_transaction_id: sequelize.INTEGER,
        }, {timestamps : false});

        this.ProductSoure = sql.define('product_source', {
            sourceid: { type: sequelize.INTEGER, primaryKey: true },
            source_description: sequelize.STRING,
        }, {timestamps : false});

        this.Products = sql.define('products', {
            barcode: { type: sequelize.STRING, primaryKey: true },
            name: sequelize.STRING,
            phonetic_name: sequelize.STRING,
            price: sequelize.DECIMAL,
            bulkid: sequelize.INTEGER,
            coffee: sequelize.BOOLEAN
        }, {timestamps : false});

        this.DynamicProducts = sql.define('dynamic_barcode_lookup', {
            barcode: { type: sequelize.STRING, primaryKey: true },
            name: sequelize.STRING,
            phonetic_name: sequelize.STRING,
            price: sequelize.DECIMAL,
            bulkid: sequelize.INTEGER,
            coffee: sequelize.BOOLEAN,
            userid: sequelize.INTEGER
        }, {timestamps : false, freezeTableName : true});

	//(dbounov): Not including profiles since its likely to be deleted.
	//TODO: Delete it.

        this.Roles = sql.define('roles', {
            userid : {type: sequelize.INTEGER, primaryKey: true },
            roles: { type: sequelize.STRING }
        }, {timestamps: false});

        this.SodaInventory = sql.define('soda_inventory', {
            slot: { type: sequelize.INTEGER, primaryKey: true, autoIncrement: true},
            count: sequelize.INTEGER,
        }, {timestamps: false});

        this.Transactions = sql.define('transactions', {
            xacttime : { type: sequelize.DATE, allowNull: false, defaultValue: sequelize.fn(dateFn)},
            userid : sequelize.INTEGER,
            xactvalue: sequelize.STRING,
            xacttype: sequelize.STRING,
            barcode: { type: sequelize.STRING, allowNull: true},
            source: sequelize.STRING,
            id: { type: sequelize.INTEGER, primaryKey: true, autoIncrement: true},
            finance_trans_id: { type: sequelize.INTEGER, allowNull: true}
        }, {timestamps: false});

	// (dbounov): For now not adding ucsd_emails. Seems potentially
	// un-needed

        this.Userbarcodes = sql.define('userbarcodes', {
            userid : { type: sequelize.INTEGER },
            barcode : { type : sequelize.STRING, primaryKey: true}
        }, {timestamps: false});

        this.Users = sql.define('users', {
            userid: { type: sequelize.INTEGER, primaryKey: true, autoIncrement: true},
            username: sequelize.STRING,
            email: sequelize.STRING,
            nickname: sequelize.STRING,
            pwd: { type: sequelize.STRING, allowNull: true},
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
            fraudulent: sequelize.BOOLEAN,
            voice_settings: sequelize.STRING
        }, {timestamps: false});
    }
}
