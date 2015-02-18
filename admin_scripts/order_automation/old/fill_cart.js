var casper = require('casper').create({
    verbose: true
});

// Open the business delivery page
casper.start('http://www2.costco.com/Browse/QuickOrderEntry.aspx?topnav=bdoff&whse=BD_578&lang=en-US&browse=1');

// Login
casper.waitForSelector("#TopNav1_LogInLink img",
       function success() {
           this.click("#TopNav1_LogInLink img");
       },
       function fail() {
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:EmailAddress']",
       function success() {
           this.click("form[name=LogIn] input[name='_ctl0:EmailAddress']");
       },
       function fail() {
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:EmailAddress']",
       function success() {
           this.click("form[name=LogIn] input[name='_ctl0:EmailAddress']");
       },
       function fail() {
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:EmailAddress']",
       function success() {
           this.click("form[name=LogIn] input[name='_ctl0:EmailAddress']");
       },
       function fail() {
   });
   casper.waitForSelector("input[name='_ctl0:EmailAddress']",
       function success() {
           this.sendKeys("input[name='_ctl0:EmailAddress']", "lami4ka@gmail.com");
       },
       function fail() {
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:Password']",
       function success() {
           this.click("form[name=LogIn] input[name='_ctl0:Password']");
       },
       function fail() {
   });
   casper.waitForSelector("input[name='_ctl0:Password']",
       function success() {
           this.sendKeys("input[name='_ctl0:Password']", "WRONGPASSWORD");
       },
       function fail() {
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:SubmitLogin']",
       function success() {
           this.click("form[name=LogIn] input[name='_ctl0:SubmitLogin']");
       },
       function fail() {
   });

// Goto order page
casper.thenOpen('http://www2.costco.com/Browse/QuickOrderEntry.aspx?topnav=bdoff&whse=BD_578&lang=en-US&browse=1');

casper.then(function(){

});

casper.run();
