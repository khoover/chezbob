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
#
# $Id: stockBob.pl,v 1.9 2001-05-22 23:34:04 mcopenha Exp $
#

# Make sure Perl can find all of our files by appending INC with the 
# path to the executable.  Makes the assumption that the location of 
# the library routines is in the parent directory.
open(TMP, "which $0 |") || die "can't do which $0: $!\n";
my $fullpath = <TMP>;
close(TMP) || die "can't close\n";
$BOBPATH = substr($fullpath, 0, rindex($fullpath, '/')) . "/..";
push(@INC, $BOBPATH);

require "dlg.pl";
require "bc_util.pl";
require "bob_db.pl";


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
      # check for proper input and then ask for quantity for stock.  
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

  while ($newStock !~ /^\d+$/) {
      $win_title = "Enter the STOCK of $newName";
      $win_text = "Please enter the amount in stock.";
      
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> ./input.product") != 0) {
	  return "";
      }
      $newStock = `cat ./input.product`;
  }
  
  &bob_db_insert_product($newBarcode, $newName, $newPhonetic_Name, $newPrice, $newStock);

  $win_title = "New Product Entered into Database";
  $win_text = "The following product has been entered:\n"
      ."Name: $newName\nPrice:$newPrice\nStock:$newStock";
  system("$DLG --title \"$win_title\" --clear --cr-wrap --msgbox \"" .
	 $win_text .
	 "\" 8 55");
  # may want to add speech here to test the voice synthesis name
}


sub
newBulk_win
{
  my ($newBarcode) = @_;
  my $newName = "";
  my @entities;

  # ASK FOR NEW NAME FOR NEW PRODUCT
  my $win_title = "New Bulk Product";
  my $win_text = " The barcode of this bulk item is not in the database." .
      " Please enter the name of this product.";
  while ($newName !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> ./input.product") != 0) {
	  return "";
      }
      $newName = `cat ./input.product`;
  }

  # ASK FOR Number of kinds of items in the bulk item
  $win_title = "# of kinds"; 
  $win_text = "Enter the number of kinds of items";
  while (!$done) {
      
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> ./input.product") != 0) {
	  return "";
      }      
      $numKinds = `cat ./input.product`;
      if ($numKinds =~ /^\d+$/) {
	  $done = 1;
      }
  }

  $done = 0;
  # for each kind, get the barcode and quantity and record in db
  for ($i=1; $i<=$numKinds; $i++) {
    $win_title = "product $i";
    $win_text = "Scan the barcode of product $i"; 
    my $done = 0;
    while (!$done) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 8 55 2> ./input.product") != 0) {
          return ""; 
      }
      $guess = `cat ./input.product`;
      $prodbarcode = &preprocess_barcode($guess);
      if(!&isa_upc_barcode($prodbarcode)) {
        &errorBarcode();
      } else {
        $done = 1;
      }
    } 

    $done = 0;
    $quan = 0;
    while (!$done) {
	$win_text = "Enter the quantity of product $i"; 
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> ./input.product") != 0) {
	    return "";
	}
	$quan = `cat ./input.product`;
	push (@entities, $prodbarcode);
	push (@entities, $quan);
	$done = 1;
    }
    &bob_db_insert_bulk_item($newBarcode, $newName, $prodbarcode, $quan);
  }
  $win_title = "New Item Entered";
  $win_text = "You have entered $newName\ninto the database.";
  $win_text = $win_text."\nProduct : Quantity per bulk";
  my %enthash = @entities;
  my $numLines = 8;
  while (($prodbarcode, $quan) = each(%enthash)) {
      my $name = &bob_db_get_productname_from_barcode($prodbarcode);
      if (defined $name) {
	  $prodbarcode = $name;
      }
      $win_text = $win_text."\n$prodbarcode : $quan";
      $numLines = $numLines + 1;
  }
  system("$DLG --title \"$win_title\" --clear --cr-wrap --msgbox \"" .
	 $win_text . "\" $numLines 55");
}


sub
oldProduct_win
{
  my ($barcode, $name, $stock) = @_;

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
	       "\" 8 55 2> ./input.barcode") != 0) {
	return "";
    }
    
    $guess = `cat ./input.barcode`;    
    $newBarcode = &preprocess_barcode($guess);    
    if(!&isa_upc_barcode($newBarcode)) {
	# case where barcode is not a barcode...
	&errorBarcode();
    } else {
	my $bulkname = &bob_db_update_products_in_bulk_item($newBarcode);
	
	if (!defined $bulkname) {
	    # bulk product not found... enter new product;
	    &newBulk_win($newBarcode);
	} else {
	    my $numLines = 8;
	    my $products = &bob_db_get_products_from_bulk_item($newBarcode);
	    my %hashproducts = @$products;
	    $win_title = "$bulkname Updated";
	    $win_text = "$bulkname has been updated";
	    $win_text = $win_text."\nProduct : Stock";
	    while (($productname, $productstock) = each (%hashproducts)) {
		$win_text = $win_text."\n$productname : $productstock";
		$numLines = $numLines + 1;
	    }
	    if ($numLines > 14) {
		$numLines = 14;
	    } 
	    system("$DLG --title \"$win_title\" --clear --cr-wrap --tab-correct --msgbox \"" .
		   $win_text .
		   "\" $numLines 55");
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
deleteBulk
{
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Delete Bulk";
    my $win_text = "Enter the barcode of the bulk item you want to DELETE.";
    
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
	    my $newName = &bob_db_get_bulk_name_from_barcode($newBarcode);
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
	    
	    &bob_db_delete_bulk($newBarcode);
	    
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
    "\"Restock Bulk\" " .
    "\"Restock products in BULK\" " .
    "\"Restock Product\" " .
    "\"Restock a SINGLE product \" " .
    "\"Delete Product\" " .
    "\"DELETE a product from the inventory\" " .
    "\"Delete Bulk\" " .
    "\"DELETE a bulk item from inventory\" " .
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
    /^Restock Bulk$/ && do {
       &enterBulkBarcode();
       last SWITCH;
    };

    /^Restock Product$/ && do {
       &enterBarcode();
       last SWITCH;
    };

    /^Delete Bulk$/ && do {
       &deleteBulk();
       last SWITCH;
    };

    /^Delete Product$/ && do {
       &deleteProduct();
       last SWITCH;
    };
  }
}

system("rm -f ./input.*");

