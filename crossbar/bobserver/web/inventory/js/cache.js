
var barcode_cache = {};

barcode_cache.item_cache = {};

barcode_cache.lookup = function(bc, cb, fail_cb) {
    if (barcode_cache.item_cache[bc] !== undefined) {
        return cb(barcode_cache.item_cache[bc]);
    }

    function add_to_cache(result) {
        barcode_cache.item_cache[bc] = result;
        cb(result);
    }

    barcode_cache.slow_lookup(bc).then(add_to_cache, fail_cb);
};

barcode_cache.init = function(lookup_function) {
    barcode_cache.slow_lookup = lookup_function;
};
