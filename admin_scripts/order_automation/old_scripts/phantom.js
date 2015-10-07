var page = require('webpage').create();

function just_wait() {
    setTimeout(function() {
                page.render('test1.png');
        }, 200000);
}

page.open('http://www2.costco.com/Browse/BDLanding.aspx?lang=en-US&Business_Delivery', function() {
    page.render('test0.png');

    page.evaluate(function(){
        document.getElementById('txtBDEnterZip').value="92093";
        document.getElementById('BDGoButton').click();
        document.getElementById('BDLanding').submit();
    });

    //just_wait();
    setTimeout(function(){page.render('test1.png');}, 10000);

    phantom.exit();
});


