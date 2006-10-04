#!/usr/bin/perl -w

# stockBob.pl
#
# Perl script that offers a quick way to insert new products and update 
# the inventory of existing products.  This specific module/program does 
# not allow the change of pricing or naming of an existing product; one 
# must first delete the product and create it anew.
#
# Wesley Leong (wleong@cs.ucsd.edu)
# Created: 5/2/01

# Make sure Perl can find all of our files by storing the path to the
# executable (stockBob) in BOBPATH
open(TMP, "which $0 |") || die "can't do which $0: $!\n";
my $fullpath = <TMP>;
close(TMP) || die "can't close\n";
$BOBPATH = substr($fullpath, 0, rindex($fullpath, '/')) . "/..";

require "$BOBPATH/dlg.pl";
require "$BOBPATH/bc_util.pl";
require "$BOBPATH/bob_db.pl";


sub
errorBarcode
{
  my $win_title = "Bad Barcode";
  my $win_text = "The input was not recognized as a valid barcode";

  system("$DLG --title \"$win_title\" --clear --msgbox \"" .
	 $win_text .
	 "\" 6 55 2> /dev/null");
  # check the number and insert it into database.
}


sub
newProduct_win
{
# Long subroutine - keeps track of all the new variables that can
# be entered in this lenghty process of entering new products.
# Breaking this subroutine into smaller ones would just require more
# parameter passing around or reqiure state saving from the main program.

  my ($newBarcode) = @_;
  my $flag = 1;
  my $newName = "";
  my $newPhonetic_Name = "";
  my $newPrice = "";

  # ASK FOR NEW NAME FOR NEW PRODUCT
  my $win_title = "New Product";
  my $win_text = q{
This is a new product.  Enter the product's name.
  };

  while ($newName !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .  "\" 8 55 2> ./input.product") != 0) {
	  return "";
      }
      $newName = `cat ./input.product`;
  }

  # ASK FOR PHONETIC NAME
  $win_title = "Phonetic Name For $newName";
  $win_text = " Please enter a PHONETIC NAME for the Speech Synthesis.";
  while ($newPhonetic_Name !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .  "\" 8 55 2> ./input.product") != 0) {
	  return "";
      }
      $newPhonetic_Name = `cat ./input.product`;
      # check for proper input
  }

  # ASK FOR PRICE
  $win_title = "Enter the PRICE of $newName";
  $win_text = "Please enter the PRICE of this item (include decimal point for cents).";
  while ($newPrice !~ /^\d*\.\d{0,2}$/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> ./input.product") != 0) {
	  return "";
      }      
      $newPrice = `cat ./input.product`;
  }

  &bob_db_insert_product($newBarcode, $newName, $newPhonetic_Name, $newPrice);

  $win_title = "New Product Entered into Database";
  $win_text = "The following product has been entered:\n"
      ."Name: $newName\nPrice:$newPrice";
  system("$DLG --title \"$win_title\" --clear --cr-wrap --msgbox \"" .
	 $win_text .
	 "\" 8 55");
  # may want to add speech here to test the voice synthesis name
}


sub
oldProduct_win
{
  my $stock = 0;
  my ($barcode, $name) = @_;

  my $win_title = "Restock an Individual Product";
  my $win_text = q{
Product Name: %s\n
Number in Stock: %d\n

Enter an amount to add to the present stock total
(Negative values are OK)
  };

  if (system("$DLG --title \"$win_title\" --clear --cr-wrap --inputbox \"" .
             sprintf($win_text, $name, $stock) .
	     "\" 14 55 2> ./input.product") != 0) {
      return "";
  }

  my $newStock = `cat ./input.product`;

  $newStock = $newStock + $stock;
  
  $win_title = "Stock Updated";
  $win_text = "You updated the stock to a new total of $newStock.";
  system("$DLG --title \"$win_title\" --clear --msgbox \"" .
	 $win_text .
	 "\" 8 55");
}


sub
enterBarcode
{
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Stock Manager: Enter Barcode";
    my $win_text = "Enter the barcode of a product";
    
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .  "\" 8 55 2> ./input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat ./input.barcode`;

	$newBarcode = &preprocess_barcode($guess);

	if(!&isa_upc_barcode($newBarcode)) {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    my $name = &bob_db_get_productname_from_barcode($newBarcode);
	    if (defined $name) {
		# assign each value in DB to a perl variable.
		&oldProduct_win($newBarcode, $name);
	    } else {
		# product not found... enter new product;
		&newProduct_win($newBarcode);
	    }
	}
}


sub
deleteProduct
{
  my $guess = "0";
  my $newBarcode = "0";
    
  my $win_title = "Delete Product";
  my $win_text = "Enter the barcode of the product you want to DELETE.";

  while (1) {
   if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
     $win_text .  "\" 8 55 2> ./input.barcode") != 0) {
     return "";
   }

	$guess = `cat ./input.barcode`;
	
	$newBarcode = &preprocess_barcode($guess);
	
	if(!&isa_upc_barcode($newBarcode)) {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    # Confirm deletion by showing the item in a confirmation dialog box.

	    # First get the name of the item
            my $newName = &bob_db_get_productname_from_barcode($newBarcode);
	    if (!defined $newName) {
	        $win_title = "Barcode Not Found";
	        $win_text = "Barcode not found in database.";
		system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		       $win_text .
		       "\" 8 55");
		return"";
	    }

	    # Then create the confirmation box
	    $win_title = "Confirm the Deletion of: $newName";
	    $win_text = "DELETE $newName?"; 
	    if (system("$DLG --title \"$win_title\" --clear --yesno \"" .
		       $win_text .
		       "\" 8 55") != 0) {
		return "";
	    }

            &bob_db_delete_product($newBarcode);

	    $win_title = "Deleted $newName";
	    $win_text = "You have just deleted $newName from the database.";
	    system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		       $win_text .
		   "\" 8 55");
	    return "";
	}
    }
}


sub
mainMenu
{
  my $win_title = "Chez Bob Inventory Manager";
  my $win_textFormat = "Welcome to the Chez Bob Inventory Management System.";

  #my $stupid = <STDIN>;

  system("$DLG --title \"$win_title\" --clear --menu \"" .
    "$win_textFormat" .
    "\" 13 60 8 " .
    "\"Restock Product\" " .
    "\"Restock a SINGLE product \" " .
    "\"Delete Product\" " .
    "\"DELETE a product from the inventory\" " .
    "\"Quit\" " .
    "\"QUIT this program\" " .
    " 2> ./input.action");
    
  my $action = `cat ./input.action`;

  if ($action eq "") {
    $action = "Quit";
  } else {
    return $action;
  }
}


&bob_db_connect;
system("rm -f ./input.*");

$action = "";

while ($action ne "Quit") {
  $action = &mainMenu();

  $_ = $action;
  SWITCH: {
    /^Restock Product$/ && do {
       &enterBarcode();
       last SWITCH;
    };

    /^Delete Product$/ && do {
       &deleteProduct();
       last SWITCH;
    };
  }
}

system("rm -f ./input.*");
system("rm -f /tmp/menuout");

