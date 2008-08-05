#!/usr/bin/perl -w

use strict;
use CGI qw/:standard/;

charset('utf-8');

my ($username, $amount);

if (param()) {
    $amount = sprintf "%.02f", param('amt');
    $username = escapeHTML(param('user'));
}

my $desc = "Debt";
$desc = "Debt ($username)" if $username;

$amount ||= "0.00";

print header;

print <<"END";
<html>
    <head>
        <title>Chez Bob Debt Repayment</title>
    </head>
    <body>
        <h1>Owe Chez Bob Money?</h1>
        <p>If you're no longer at UCSD, payment can be mailed to:</p>
        <blockquote>Chez Bob, c/o Michael Vrable<br />
        UCSD Department of Computer Science and Engineering<br />
        9500 Gilman Drive, Mail Code 0404<br />
        La Jolla, CA 92093-0404</blockquote>
        <p>Checks should be made out to Michael Vrable.</p>

END

print <<"END" if $username;
        <hr />
        <p>Or, you can use Google Checkout to make a payment to account <b>$username</b>:</p>
        <form action="https://checkout.google.com/cws/v2/Merchant/109618549353329/checkoutForm" id="BB_BuyButtonForm" method="post" name="BB_BuyButtonForm">
        <input name="item_name_1" type="hidden" value="$desc"/>
        <input name="item_description_1" type="hidden" value="Services Rendered"/>
        <input name="item_quantity_1" type="hidden" value="1"/>

        \$<input name="item_price_1" value="$amount"/>
        <input name="item_currency_1" type="hidden" value="USD"/>
        <input name="_charset_" type="hidden" value="utf-8"/>
        <input alt="" src="https://checkout.google.com/buttons/buy.gif?merchant_id=109618549353329&amp;w=117&amp;h=48&amp;style=white&amp;variant=text&amp;loc=en_US" type="image"/>
        </form>
END

print <<"END";
    </body>
</html>
END
