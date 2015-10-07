/*==============================================================================*/
/* Casper generated Mon Nov 17 2014 12:55:41 GMT-0800 (PST) */
/*==============================================================================*/

var x = require('casper').selectXPath;
casper.options.viewportSize = {width: 720, height: 741};
casper.options.userAgent = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Ubuntu Chromium/38.0.2125.111 Chrome/38.0.2125.111 Safari/537.36";
casper.options.verbose = true;
casper.options.logLevel = "debug";
casper.on('page.error', function(msg, trace) {
   this.echo('Error: ' + msg, 'ERROR');
   for(var i=0; i<trace.length; i++) {
       var step = trace[i];
       this.echo('   ' + step.file + ' (line ' + step.line + ')', 'ERROR');
   }
});
casper.test.begin('Resurrectio test', function(test) {
   casper.start('http://www2.costco.com/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US');
   casper.thenOpen('http://www2.costco.com/Browse/QuickOrderEntry.aspx?whse=BD_578&lang=en-US');
   casper.waitForSelector("#TopNav1_LogInLink img",
       function success() {
           test.assertExists("#TopNav1_LogInLink img");
           this.click("#TopNav1_LogInLink img");
       },
       function fail() {
           test.assertExists("#TopNav1_LogInLink img");
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:EmailAddress']",
       function success() {
           test.assertExists("form[name=LogIn] input[name='_ctl0:EmailAddress']");
           this.click("form[name=LogIn] input[name='_ctl0:EmailAddress']");
       },
       function fail() {
           test.assertExists("form[name=LogIn] input[name='_ctl0:EmailAddress']");
   });
   casper.waitForSelector("input[name='_ctl0:EmailAddress']",
       function success() {
           this.sendKeys("input[name='_ctl0:EmailAddress']", "brown.farinholt@gmail.com");
       },
       function fail() {
           test.assertExists("input[name='_ctl0:EmailAddress']");
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:Password']",
       function success() {
           test.assertExists("form[name=LogIn] input[name='_ctl0:Password']");
           this.click("form[name=LogIn] input[name='_ctl0:Password']");
       },
       function fail() {
           test.assertExists("form[name=LogIn] input[name='_ctl0:Password']");
   });
   casper.waitForSelector("input[name='_ctl0:Password']",
       function success() {
           this.sendKeys("input[name='_ctl0:Password']", "WRONGPASSWORD");
       },
       function fail() {
           test.assertExists("input[name='_ctl0:Password']");
   });
   casper.waitForSelector("form[name=LogIn] input[name='_ctl0:SubmitLogin']",
       function success() {
           test.assertExists("form[name=LogIn] input[name='_ctl0:SubmitLogin']");
           this.click("form[name=LogIn] input[name='_ctl0:SubmitLogin']");
       },
       function fail() {
           test.assertExists("form[name=LogIn] input[name='_ctl0:SubmitLogin']");
   });
   /* submit form */
   // casper.waitForSelector("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']",
   //     function success() {
   //         test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']");
   //         this.click("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']");
   //     },
   //     function fail() {
   //         test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']");
   // });
   /* submit form */
   casper.waitForSelector("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']",
       function success() {
           test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']");
           this.click("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']");
       },
       function fail() {
           test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']");
   });
   casper.waitForSelector("input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']",
       function success() {
           this.sendKeys("input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']", "1");
       },
       function fail() {
           test.assertExists("input[name='QuickOrderEntry1:QuickOrderList:_ctl1:ItemNo']");
   });
   casper.waitForSelector("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']",
       function success() {
           test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']");
           this.click("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']");
       },
       function fail() {
           test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']");
   });
   casper.waitForSelector("input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']",
       function success() {
           this.sendKeys("input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']", "1");
       },
       function fail() {
           test.assertExists("input[name='QuickOrderEntry1:QuickOrderList:_ctl1:Qty']");
   });
   casper.waitForSelector("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']",
       function success() {
           test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']");
           this.click("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']");
       },
       function fail() {
           test.assertExists("form[name=OrderbyItemNo] input[name='QuickOrderEntry1:AddToOrder1']");
   });
   /* submit form */

   casper.run(function() {test.done();});
});