# library.pl
#
# a minimal set of routines for checking out books 
#
# $Id: library.pl,v 1.1 2001-05-19 23:51:19 mcopenha Exp $
#

require "bob_db.pl";

sub
checkout_book
{
  my ($userid, $username) = @_;

  my $guess = &get_barcode_win;
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
      # email Julie or something
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

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .  "\" 6 50 2> /dev/null");
}

1;
