#!/usr/bin/perl -w

### libraries and constants
use Pg;
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


###############################################################################
# SUBROUTINES
###############################################################################


sub
isa_barcode
{
    my ($rawInput) = @_;
    if ($rawInput =~ /^\.C/)
    {
	my @getParsed = split /\./,$rawInput;
	my $numToken = @getParsed;
	if ($numToken == 4) {
	    return 1;
	}
    }
    return 0;
}

sub
decode_barcode {
    my ($rawInput) = @_;

    # this skips the barcode type stuff.
    my @getParsed = split /\./,$rawInput;
    my $rawBarcode = $getParsed[3];
    $rawBarcode =~ tr/a-zA-Z0-9+-/ -_/;
    $rawBarcode = unpack 'u', chr(32 + length($rawBarcode) * 3/4) 
	. $rawBarcode;
    $rawBarcode =~ s/\0+$//;
    $rawBarcode ^= "C" x length($rawBarcode);
    return $rawBarcode;
}


########################################
# verifyAndDecodeAnyBarcode - takses any barcode whether cuecat or character and verifies it.
# Only returns barcode that detects 12 digits or 8 digits.
########################################
sub
verifyAndDecodeAnyBarcode
{
    my ($guess) = @_;    
    if (&isa_barcode($guess)) {
	$guess = &decode_barcode($guess);
    }
    if (($guess =~/^\d{12}$/) || ($guess =~ /^\d{7}$/)) {
	return $guess;
    }
    else {
	# Bad input
	return "";
    }
}


########################################
# errorBarcode
########################################
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


########################################
# newProduct_win
########################################
sub
newProduct_win
{
# Long subroutine - keeps track of all the new variables that can
# be entered in this lenghty process of entering new products.
# Breaking this subroutine into smaller ones would just require more
# parameter passing around or reqiure state saving from the main program.

  my ($conn, $newBarcode) = @_;
  my $win_title = "New Product";
  my $win_text = " The barcode to this product is not in the database." .
      "This is a new product. Please enter the name of this product.";
  my $flag = 1;
  my $newName = "";
  my $newPrice = "";
  my $newStock = "";

  while ($newName !~ /\w+/) {
      if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		 $win_text .
		 "\" 12 55 2> /tmp/input.product") != 0) {
	  return "";
      }
      $newName = `cat /tmp/input.product`;
      system("rm -f /tmp/input.product");
      # check for proper input and then ask for quantity for stock.  
      $win_title = "Enter the PRICE of $newName";
      $win_text = "Please enter the PRICE of this item (include decimal point for cents).";
  }

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
  
  my $insertqueryFormat = q{
      insert into products
	  values(
		 '%s',
		 '%s',
		 %.2f,
		 %d
		 );
  };

  my $result = $conn->exec(sprintf($insertqueryFormat,
				   $newBarcode,
				   $newName,
				   $newPrice,
				   $newStock));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
      print STDERR "add_win: error inserting record...exiting\n";
      exit 1;
  }
  $win_title = "New Product Entered into Database";
  $win_text = "The following product has been entered:\n"
      ."Name: $newName\nPrice:$newPrice\nStock:$newStock";
  system("$DLG --title \"$win_title\" --clear --msgbox \"" .
	 $win_text .
	 "\" 9 55");
}


########################################
# oldProduct_win
########################################
sub
oldProduct_win
{
  my ($conn, $newBarcode, $name, $price, $stock) = @_;
  my $win_title = "$name";
  my $win_text = "Product Name: $name.\n".
      " Please enter new stock total.";

  if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	     $win_text .
	     "\" 8 55 2> /tmp/input.product") != 0) {
      return "";
  }

  my $newStock = `cat /tmp/input.product`;
  system("rm -rf /tmp/input.product");

  # check the number and update the database.
  my $updatequeryFormat = q{
      update products
	  set stock = %d
	      where barcode = '%s';
  };

  my $result = $conn->exec(sprintf($updatequeryFormat,
				   $newStock,
				   $newBarcode));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
      print STDERR "add_win: error updating record...exiting\n";
      exit 1;
  }
  $win_title = "Stock Updated";
  $win_text = "You have updated the stock to $newStock.";
  system("$DLG --title \"$win_title\" --clear --msgbox \"" .
	 $win_text .
	 "\" 8 55");
}


########################################
# enterBarcode
########################################
sub
enterBarcode
{
    my ($conn) = @_;
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Stock Manager: Enter Barcode";
    my $win_text = "Enter the barcode of a product";
    
    while (1) {
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");

	$newBarcode = &verifyAndDecodeAnyBarcode($guess);

	if($newBarcode eq "") {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    my $selectqueryFormat = q{
		select *
		    from products
			where barcode = '%s';
	    };
	    my $result = $conn->exec(sprintf($selectqueryFormat,
					     $newBarcode));
	    if ($result->ntuples == 1) {
		# assign each value in DB to a perl variable.
		$newBarcode = $result->getvalue(0,0);
		my $name = $result->getvalue(0,1);
		my $price = $result->getvalue(0,2);
		my $stock  = $result->getvalue(0,3);
		&oldProduct_win($conn,
				$newBarcode,
				$name,
				$price,
				$stock);
		#return $newBarcode;
	    } else {
		# product now found... enter new product;
		&newProduct_win($conn, $newBarcode);
		#return $newBarcode;
	    }
	}
    }
}


########################################
# deleteProduct
########################################
sub
deleteProduct
{
    my ($conn) = @_;
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Stock Manager: Delete Product";
    my $win_text = "Enter the barcode of the product you want to DELETE.";

    while (1) {
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");
	
	$newBarcode = &verifyAndDecodeAnyBarcode($guess);
	
	if($newBarcode eq "") {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    # Confirm deletion by showing the item in a confirmation dialog box.

	    # First get the name of the item
	    my $selectqueryFormat = q{
		select name
		    from products
			where barcode = '%s';
	    };
	    my $result = $conn->exec(sprintf($selectqueryFormat, $newBarcode));
	    $win_title = "Barcode Not Found";
	    $win_text = "Barcode not found in database.";
	    if ($result->ntuples != 1) {
		system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		       $win_text .
		       "\" 8 55");
		return"";
	    }

	    my $newName = $result->getvalue(0,0);
	    # Then create the confirmation box
	    $win_title = "Confirm the Deletion of: $newName";
	    $win_text = "DELETE $newName?"; 
	    if (system("$DLG --title \"$win_title\" --clear --yesno \"" .
		       $win_text .
		       "\" 8 55") != 0) {
		return "";
	    }

	    my $deletequeryFormat = q{
		delete
		    from products
			where barcode = '%s';
			};
	    $result = $conn->exec(sprintf($deletequeryFormat,
					  $newBarcode));
	    if ($result->resultStatus != PGRES_COMMAND_OK) {
		print STDERR "delete_win: error deleting record...exiting\n";
		exit 1;
	    }
	    $win_title = "Deleted $newName";
	    $win_text = "You have just deleted $newName from the database.";
	    system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		       $win_text .
		   "\" 8 55");
	    return "";
	}
    }
}


########################################
# ChangeName
########################################
sub
changeName
{
    my ($conn) = @_;
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Stock Manager: Change Name";
    my $win_text = "Enter the barcode of the product you want to change the NAME of.";

    while (1) {
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");
	
	$newBarcode = &verifyAndDecodeAnyBarcode($guess);
	
	if($newBarcode eq "") {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    # Confirm deletion by showing the item in a confirmation dialog box.

	    # First get the name of the item
	    my $selectqueryFormat = q{
		select name
		    from products
			where barcode = '%s';
	    };
	    my $result = $conn->exec(sprintf($selectqueryFormat, $newBarcode));
	    $win_title = "Barcode Not Found";
	    $win_text = "Barcode not found in database.";
	    if ($result->ntuples != 1) {
		system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		       $win_text .
		       "\" 8 55");
		return"";
	    }	    

	    my $name = $result->getvalue(0,0);
	    # Then create the confirmation box
	    $win_title = "Changing the Name of $name";
	    $win_text = "Change the NAME from $name to what?"; 
	    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		       $win_text .
		       "\" 8 55 2> /tmp/input.name") != 0) {
		return "";
	    }	    

	    my $newName = `cat /tmp/input.name`;
	    system("rm -rf /tmp/input.name");

	    my $updatequeryFormat = q{
		update products
		    set name = '%s'
			where barcode = '%s';
	    };
	    $result = $conn->exec(sprintf($updatequeryFormat,
					  $newName,
					  $newBarcode));
	    if ($result->resultStatus != PGRES_COMMAND_OK) {
		print STDERR "update_win: error deleting record...exiting\n";
		exit 1;
	    }
	    $win_title = "Changed $name to $newName";
	    $win_text = "Changed the name from:\n$name => $newName";

	    system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		   $win_text .
		   "\" 8 55");
	    return "";
	}
    }
}


########################################
# ChangePrice
########################################
sub
changePrice
{
    my ($conn) = @_;
    my $guess = "0";
    my $newBarcode = "0";
    
    my $win_title = "Stock Manager: Change Price";
    my $win_text = "Enter the barcode of the product you want to change".
	"the PRICE of.";

    while (1) {
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");
	
	$newBarcode = &verifyAndDecodeAnyBarcode($guess);
	
	if($newBarcode eq "") {
	    # case where barcode is not a barcode...
	    &errorBarcode();
	} else {
	    # Confirm deletion by showing the item in a confirmation dialog box.

	    # First get the name of the item
	    my $selectqueryFormat = q{
		select name, price 
		    from products
			where barcode = '%s';
	    };
	    my $result = $conn->exec(sprintf($selectqueryFormat, $newBarcode));
	    $win_title = "Barcode Not Found";
	    $win_text = "Barcode not found in database.";
	    if ($result->ntuples != 1) {
		system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		       $win_text .
		       "\" 8 55");
		return"";
	    }	    

	    my $name = $result->getvalue(0,0);
	    my $price = $result->getvalue(0,1);
	    # Then create the confirmation box
	    $win_title = "Changing the PRICE of $name";
	    $win_text = "Change the PRICE of $name from $price to what?\n".
		"(include decimals for cents)"; 

	    my $newPrice = "";
	    do {
		if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
			   $win_text .
			   "\" 8 55 2> /tmp/input.name") != 0) {
		    return "";
		}	    
		
		$newPrice = `cat /tmp/input.name`;
		system("rm -rf /tmp/input.name");
	    } while ($newPrice !~ /^\d*\.\d{0,2}$/);

	    my $updatequeryFormat = q{
		update products
		    set price = '%s'
			where barcode = '%s';
	    };
	    $result = $conn->exec(sprintf($updatequeryFormat,
					  $newPrice,
					  $newBarcode));
	    if ($result->resultStatus != PGRES_COMMAND_OK) {
		print STDERR "update_win: error deleting record...exiting\n";
		exit 1;
	    }
	    $win_title = "Changed the Price From $price to $newPrice";
	    $win_text = "Changed the price of $name from:\n$price => $newPrice";

	    system("$DLG --title \"$win_title\" --clear --msgbox \"" .
		   $win_text .
		   "\" 8 55");
	    return "";
	}
    }
}


########################################
# mainMenu - the big front menu
########################################
sub
mainMenu
{
    my $win_title = "Chez Bob Inventory Manager";
    my $win_textFormat = "Welcome to Chez Bob Inventory Management System.";

    my $retval =
	system("$DLG --title \"$win_title\" --clear --menu \"" .
	       "$win_textFormat".
	       "\" 14 64 8 " .
	       "\"Stock\" " .
	       "\"STOCK Chez Bob Inventory \" " .
	       "\"Change Price\" " .
	       "\"Change the PRICE of a Chez Bob product \" " .
	       "\"Change Name\" " .
	       "\"Change the NAME of a Chez Bob product \" " .
	       "\"Delete\" " .
	       "\"DELETE a Chez Bob product \" " .
	       "\"Inventory\" " .
	       "\"Turn inventory system on or off \" " .
	       "\"Quit\" " .
	       "\"QUIT this program\" " .
	       " 2> /tmp/input.action");
    
    my $action = `cat /tmp/input.action`;
    system("rm -f /tmp/input.*");
    if ($action eq "")
    {
	$action = "Quit";
    }
    return $action;
}


###############################################################################
# MAIN PROGRAM
###############################################################################

$conn = Pg::connectdb("dbname=bob");
if ($conn->status == PGRES_CONNECTION_BAD) {
    print STDERR "MAIN: error connecting to database...exiting.\n";
    print STDERR $conn->errorMessage;
    exit 1;
}

$action = "";

while ($action ne "Quit") {
    $action = &mainMenu();

    if ($action eq "Delete") {
	&deleteProduct($conn);
    }
    elsif ($action eq "Stock") {
	&enterBarcode($conn);
    }
    elsif ($action eq "Change Name") {
	&changeName($conn);
    }
    elsif ($action eq "Change Price") {
	&changePrice($conn);
    }
    elsif ($action eq "Inventory") {
	
    }
}
