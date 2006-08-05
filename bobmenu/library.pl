# library.pl
#
# a minimal set of routines for checking out books.  I obtained a nice
# set of python scripts (http://eblong.com/zarf/bookscan/) that can take a 
# list of EBN (or UPC) barcodes from books, convert them into ISBN #'s,
# look up the ISBN's on Amazon, and finally output a tab-delimited text
# file containing the author(s) and title of every book.  
#
# To make this really useful we'd need to add a database table that 
# records which user checked out a book, the date checked out, due date,
# etc.  We may also send mail to the head librarian (Julie?). 

require "$BOBPATH/bob_db.pl";


sub
checkout_book
{
  my ($userid, $username) = @_;

  my $msg = q{
Scan the barcode on the back side of the book. 
If there is more than one, scan the barcode that 
begins with '978'.};
  my $guess = &get_barcode_win($msg, 55, 11);
  if (!defined $guess) { 
    # User canceled
    return;
  }
  
  my $barcode = &preprocess_barcode($guess);      
  my $book = &bob_db_get_book_from_barcode($barcode);
  if (!defined $book) {
    &invalid_book_barcode_win;
  } else {
    ($authors, $title) = split(/\t/, $book);
    my $msg = "$title by\n$authors?";
    if (&confirm_win("Checkout the following book?", $msg, 60, 8)) {
      # email Julie or something; for now just call report
      &report("book checkout", "$username checked out:\n$msg");
    } else {
      return;
    }
  }
}
    

sub
invalid_book_barcode_win
{
  my $win_title = "Book Not Found";
  my $win_text = q{
I could not find this book.};

  &get_dialog_result("--title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 6 50");
}

1;
