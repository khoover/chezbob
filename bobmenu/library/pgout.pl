#!/usr/bin/perl -w

# a little script to insert data into postgres db
# Michael Copenhafer (mcopenha@cs)

use Pg;
require "../bob_db.pl";

open(BC, "barcodes");
open(ISBN, "isbn");
open(BOOKS, "books");

&bob_db_connect;

while (<BC>) {
  chomp($barcode = $_);
  chomp($isbn = <ISBN>);
  my @book = split(/\t/, <BOOKS>);
  chomp($author = $book[0]);
  chomp($title = $book[1]);

  &bob_db_insert_book($barcode, $isbn, $author, $title);
#  $testbook = &bob_db_get_book_from_barcode($barcode);
#  print($testbook);

  print "$barcode\n";
  print "$isbn\n";
  print "$author\n";
  print "$title\n\n";
}
