#!/usr/bin/perl -w

### libraries and constants
use Pg;
$DLG = "/usr/bin/dialog";

###############################################################################
# SUBROUTINES
###############################################################################


sub
isa_barcode
{
    my ($rawInput) = @_;
    if ($rawInput =~ /^\.C/)
    {
	return 1;
    } else {
	return 0;
    }   
}

sub
decode_barcode {
    my ($rawInput) = @_;

    split
    printf "Serial: %s  Type: %s  Code: %s\n",
    map {
        tr/a-zA-Z0-9+-/ -_/;
        $_ = unpack 'u', chr(32 + length() * 3/4) . $_;
        s/\0+$//;
        $_ ^= "C" x length;
    } /\.([^.]+)/g;
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
      $win_text = "Please enter the PRICE of this item.";
  }

  while ($newPrice !~ /^\d+$/ && $newPrice !~ /^\d*\.\d{0,2}$/) {

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

  # check the number and update the database.
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

    $win_title = "Stock Manager: Enter Barcode";
    $win_text = "Enter the Barcode of a Product";

    while (1) {
	if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
		   $win_text .
		   "\" 8 55 2> /tmp/input.barcode") != 0) {
	    return "";
	}
	
	$guess = `cat /tmp/input.barcode`;
	system("rm -f /tmp/input.barcode");
	if (&isa_barcode($guess)) {
	    $newBarcode = &decode_barcode($guess);      
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
		return $newBarcode;		
	    }
	    # product now found... enter new product;
	    &newProduct_win($conn, $newBarcode);
	    return $newBarcode;
	}
	# case where barcode is not a barcode...
	&errorBarcode();
    }
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

&enterBarcode($conn);
