var barcode_catcher = {};

barcode_catcher.TIMEOUT_THRESHOLD = 5000;

barcode_catcher.init = function(callback) {
    var buffer = "";
    var ts = Date.now();

    document.onkeypress = function(obj) {
        var buffer_base = buffer;
        if (Date.now() - ts >= barcode_catcher.TIMEOUT_THRESHOLD) {
            buffer_base = "";
        }

        if (obj.key == "Enter") {
            if (buffer !== "") {
                callback(buffer);
            }
            buffer = "";
        }
        else {
            buffer = buffer_base + obj.key;
            ts = Date.now();
        }
    };

    console.log("Initialized barcode catcher.");
};
