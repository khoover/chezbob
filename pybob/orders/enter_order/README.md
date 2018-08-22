The purpose of this directory is to help you to enter "orders" in the Chez Bob
system.

Note:
 - It is NOT for deciding WHAT to order. That's an "order estimate"
 - It is NOT for doing the ordering from Costco. That's "order automation".
 - It is NOT for scanning orders as they come in. That's "accept[ing an] order".

This script is for helping Bob know what you ultimately tried to buy from
Costco, and for updating prices accordingly. This preps the Chez Bob system to
accept the order with the barcode scanners.

You provide it with Costco's status page of what you ordered (which may be less
than you wanted to order, since something was inevitably out of stock), and
enters it into the database.

It does that in two steps. In the first step, you generate an intermediate text
file that the second step consumes. That's because extracting the data changes
all the time, and we briefly did email parsing in awk.

# Ok, let's do it:

This is the step that breaks all the time.

Go grab the soruce for the Order Details page on CostcoBusinessDelivery.com for
this order. Save it somewhere, e.g., orders/%y%m%d.html

Then convert it to the intermediate representation. As of March 2018, that's
done via:

    $ ./order_status_page_to_order_file.py < orders/180309.html > orders/180309.txt

If it works, you'll get lines that look like this:
```
    5658 1 $10.59
    1013852 1 $10.99
    966484 1 $13.99
    ...
```
(which is in the format of (Costco ID, Quantity, Price-Per-Each)-tuples)

# Update prices and insert order

Use the `add_order` script to insert the order. It supports the `-h` flag, so
learn more there. Here's an example:

    $ ./add_order -d "Joe DeBlasio: Costco" -u orders/180309.txt 2018-03-09

Now use the admin interface to make sure everything looks OK. It'll usually get
things a bit wrong, e.g. the total purchase amount will be wrong, and it might
have issues with sales tax, discounts, etc..

