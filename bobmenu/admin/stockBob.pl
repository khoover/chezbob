#!/usr/bin/perl -w

$DLG = "/usr/bin/dialog";

###############################################################################
# stockBob.pl
#
# DESCRIPTION:
# Perl script that offers a quick way to insert new products
# and update the inventory of existing products.
# This specific module/program does not allow the change of pricing or naming
# of an existing product.
###############################################################################

do 'bc_util.pl';
do 'bob_db.pl';


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
  my $newStock = "";

  # ASK FOR NEW NAME FOR NEW PRODUCT
  my $win_title = "New Product";
  my $win_text = q{
This is a new product.  Enter the product's name.
  };

  while ($newName !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .  "\" 12 65 2> /tmp/input.product") != 0) {
	  return "";
      }
      $newName = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");
  }

  # ASK FOR PHONETIC NAME
  $win_title = "Phonetic Name For $newName";
  $win_text = " Please enter a PHONETIC NAME for the Speech Synthesis.";
  while ($newPhonetic_Name !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .  "\" 12 55 2> /tmp/input.product") != 0) {
	  return "";
      }
      $newPhonetic_Name = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");
      # check for proper input and then ask for quantity for stock.  
  }

  # ASK FOR PRICE
  $win_title = "Enter the PRICE of $newName";
  $win_text = "Please enter the PRICE of this item (include decimal point for cents).";
  while ($newPrice !~ /^\d*\.\d{0,2}$/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> /tmp/input.product") != 0) {
	  return "";
      }      
      $newPrice = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");      
  }

  while ($newStock !~ /^\d+$/) {
      $win_title = "Enter the STOCK of $newName";
      $win_text = "Please enter the amount in stock.";
      
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> /tmp/input.product") != 0) {
	  return "";
      }
      $newStock = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");
  }
  
  &bob_db_insert_product($newBarcode, $newName, $newPhonetic_Name, $newPrice, $newStock);

  $win_title = "New Product Entered into Database";
  $win_text = "The following product has been entered:\n"
      ."Name: $newName\nPrice:$newPrice\nStock:$newStock";
  system("$DLG --title \"$win_title\" --clear --msgbox \"" .
	 $win_text .
	 "\" 9 55");
  # may want to add speech here to test the voice synthesis name
}


sub
newBulk_win
{
  my ($newBarcode) = @_;
  my $newName = "";

  # ASK FOR NEW NAME FOR NEW PRODUCT
  my $win_title = "New Bulk Product";
  my $win_text = " The barcode of this bulk item is not in the database." .
      "Please enter the name of this product.";
  while ($newName !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 12 55 2> /tmp/input.product") != 0) {
	  return "";
      }
      $newName = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");
  }

  # ASK FOR Number of kinds of items in the bulk item
  $win_title = "# of kinds"; 
  $win_text = "Enter the number of kinds of items";
  while (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> /tmp/input.product") != 0) {} 
  $numKinds = `cat /tmp/input.product`;
  system("rm -f /tmp/input.product");      

  # for each kind, get the barcode and quantity and record in db
  for ($i=1; $i<=$numKinds; $i++) {
    $win_title = "product $i";
    $win_text = "Scan the barcode of product $i"; 
    my $done = 0;
    while (!$done) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> /tmp/input.product") != 0) {
          return ""; 
      }
      $guess = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");      
      $prodbarcode = &verify_and_decode_barcode($guess);
      if($prodbarcode eq "") {
        &errorBarcode();
      } else {
        $done = 1;
      }
    } 

    $win_text = "Enter the quantity of product $i"; 
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> /tmp/input.product") != 0) {
        return "";
    }
    $quan = `cat /tmp/input.product`;
    system("rm -f /tmp/input.product");      

    &bob_db_insert_bulk_item($newBarcode, $newName, $prodbarcode, $quan);
  }
}


sub
oldProduct_win
{
  my ($barcode, $name, $stock) = @_;

  my $win_title = "Restock an Individual Product";
  my $win_text = q{
Product Name: %s
Number in Stock: %d

Enter an amount to add to the present stock total
(Negative values are OK)
  };

  if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
             sprintf($win_text, $name, $stock) .
	     "\" 14 65 2> /tmp/input.product") != 0) {
      return "";
  }

  my $newStock = `cat /tmp/input.product`;
  system("rm -f /tmp/input.product");

  $newStock = $newStock + $stock;
  &bob_db_set_stock($barcode, $newStock);
  
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
		   $win_text .  "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");

	$newBarcode = &verify_and_decode_barcode($guess);

	if($newBarcode eq "") {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    my $name = &bob_db_get_productname_from_barcode($newBarcode);
	    if (defined $name) {
		# assign each value in DB to a perl variable.
		my $stock = &bob_db_get_stock_from_barcode($newBarcode);
		&oldProduct_win($newBarcode, $name, $stock);
	    } else {
		# product not found... enter new product;
		&newProduct_win($newBarcode);
	    }
	}
}

sub
enterBulkBarcode
{
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Stock Manager: Enter Barcode";
    my $win_text = "Enter the barcode of a product";
    
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");

	$newBarcode = &verify_and_decode_barcode($guess);

	if($newBarcode eq "") {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
            my $bulkname = &bob_db_update_products_in_bulk_item($newBarcode);

            if (!defined $bulkname) {
		# bulk product not found... enter new product;
		&newBulk_win($newBarcode);
	    } else {
	        system("$DLG --msgbox \"$bulkname update complete\" 8 30"); 
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
     $win_text .  "\" 8 55 2> /tmp/input.barcode") != 0) {
     return "";
   }

	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");
	
	$newBarcode = &verify_and_decode_barcode($guess);
	
	if($newBarcode eq "") {
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

  system("$DLG --title \"$win_title\" --clear --menu \"" .
    "$win_textFormat" .
    "\" 13 60 8 " .
    "\"Restock Bulk\" " .
    "\"Restock products in BULK\" " .
    "\"Restock Product\" " .
    "\"Restock a SINGLE product \" " .
    "\"Delete Product\" " .
    "\"DELETE a product from the inventory\" " .
    "\"Quit\" " .
    "\"QUIT this program\" " .
    " 2> /tmp/input.action");
    
  my $action = `cat /tmp/input.action`;
  system("rm -f /tmp/input.action");

  if ($action eq "") {
    $action = "Quit";
  } else {
    return $action;
  }
}


&bob_db_connect;

$action = "";

while ($action ne "Quit") {
  $action = &mainMenu();

  $_ = $action;
  SWITCH: {
    /^Restock Bulk$/ && do {
       &enterBulkBarcode();
       last SWITCH;
    };

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
