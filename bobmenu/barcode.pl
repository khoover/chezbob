
use Pg;

$DLG = "/usr/bin/dialog";

sub
isa_barcode
#
# Return true if 'str' contains cuecat header
#
{
  my ($str) = @_;
  return ($str =~ "^\\.C"); 
}

sub
decode_barcode
#
# Larry Wall's amazing hack to decode cuecat headers adapted by Wesley
#
{
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

sub
invalidBarcode_win
{
  my ($txt) = @_;
  my $win_title = $txt;
  my $win_text = q{
Invalid barcode.  Please try again.};

  system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .
	 "\" 9 50 2> /dev/null");
}

sub
barcode_win
#
# Prompt the user to enter a new barcode. If it's already in the database 
# (under a different userid) or is not a valid barcode, output an error msg
# and ask the user to try again. 
#
{
  my ($username, $userid, $conn) = @_;
  my $guess = '0';
  my $newBarcode = '0';
  my $win_title = "New barcode";
  my $win_text = "Scan your barcode:";

  while (1) {
    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
               $win_text .
	       "\" 8 45 2> /tmp/input.barcode") != 0) {
      return "";
    }

    $guess = `cat /tmp/input.barcode`;
    system("rm -f /tmp/input.barcode");

    if (&isa_barcode($guess)) {
      $newBarcode = &decode_barcode($guess);      
      my $selectqueryFormat = q{
        select userid
        from users
        where userbarcode = '%s';
      };
      my $result = $conn->exec(sprintf($selectqueryFormat, $newBarcode));
      if ($result->ntuples == 1) {
        if ($result->getvalue(0,0) != $userid) {
          invalidBarcode_win($newBarcode);
          next;
        }
      }
   
      my $updatequeryFormat = q{
        update users
  	set userbarcode = '%s'
        where userid = %d;
      };      
      $result = $conn->exec(sprintf($updatequeryFormat,
  				     $newBarcode,
				     $userid));
      if ($result->resultStatus != PGRES_COMMAND_OK) {
        print STDERR "barcode_win: error updating new barcode\n";
        exit 1;
      }       
      system ("$DLG --title \"$newBarcode\""
              ." --clear --msgbox"
              ." \"Barcode updated successfully!\" 9 50");
      return $newBarcode;
    } else {
      invalidBarcode_win($guess);
      next;
    }
  }
}

sub 
update_balance
{
  my ($userid,$total) = @_;
  
  $updatequeryFormat = q{
    update balances   
    set balance = balance - %.2f
    where userid = %d;
  };
  $result = $conn->exec(sprintf($updatequeryFormat, $total, $userid));
  if ($result->resultStatus != PGRES_COMMAND_OK) {
    print STDERR "record_transaction: error update record...exiting\n";
    exit 1;
  }
}

sub
update_stock
{
  my (@trans) = @_;
 
  foreach $item (@trans) {
    $updatequeryFormat = q{
      update products
      set stock = stock - 1
      where name = '%s';
    };
    $result = $conn->exec(sprintf($updatequeryFormat, $item));
    if ($result->resultStatus != PGRES_COMMAND_OK) {
      print STDERR "record_transaction: error update record...exiting\n";
      exit 1;
    }
  }
}

sub
saytotal
{
  my ($total) = @_;

  my $str = sprintf("%.2f", $total);
  my @money = split(/\./, $str);
  my $dollars = int($money[0]);
  my $cents = $money[1];
  if (substr($cents, 0, 1) eq "0") {
    $cents = chop($cents);
  }

  if ($dollars > 0) {
    &sayit("your total is \\\$$dollars and $cents cents");
  } else {
    &sayit("your total is $cents cents");
  }
}

sub
sayit
{
  my ($str) = @_;
  system("echo $str > /dev/speech");
}

sub
barcode_action_win
#
# Nasty proc that shows the main menu in barcode mode.  Keeps a running 
# tally of the products you've purchased and echoes them to the screen.
# When user hits OK or scans the 'Done' barcode the entire transaction
# is recorded (update balance and products tables). 
#
{
  my ($username,$userid,$conn) = @_;
  my $guess = '0';
  my $win_title = "Main Menu";

  my $leng = 24;	# initial dialog length 
  my $balance = &bob_db_get_balance($userid);
  my $numbought = 0;

  my $balanceString = "";
  if ($balance < 0.0) {
    $balanceString = sprintf("owe Bob \\\$%.2f", -$balance);
  } else {
    $balanceString = sprintf("have a credit balance of \\\$%.2f", $balance);
  }

  my $msg = "";
  if (-r "/tmp/message") {
    chop($msg = `cat /tmp/message`);
  }

  &sayit("Welcome $username");
  if ($balance < -5.0) {
    &sayit("It is time you deposited some money");
  }

  while (1) {
    my $win_textFormat = q{
Welcome, %s!

USER INFORMATION:
  You currently %s
  %s
  %s

Please scan each product's barcode.  When you're done,
scan the barcode at the top of the monitor labeled 'done'. 
The transaction will not be recorded until then. \n
		Product			Price
		-------			-----
};

    my $total = 0.00;
    for ($i = 0; $i < $numbought; ++$i) {
      $win_textFormat .= "\t\t" . $purchase[$i];
      my $leng = length($purchase[$i]);
      if ($leng < 8) {
        $win_textFormat .= "\t\t\t"; 
      } elsif ($leng < 16) {
        $win_textFormat .= "\t\t"; 
      } else {
        $win_textFormat .= "\t"; 
      }

      $win_textFormat .= sprintf("%.2f", $prices[$i]) . "\n";
      $total += $prices[$i];
    }
    if ($total > 0) {
      $win_textFormat .= "\t\t\t\t\t-----";
      $win_textFormat .= sprintf("\n\t\t\t\tTOTAL:\t\\\$%.2f\n", $total);
    }

    if (system("$DLG --title \"$win_title\" --clear --inputbox \"" .
	   sprintf($win_textFormat, $username,
		   $balanceString, "", $msg) .
	       "\" $leng 65 2> /tmp/input.barcode") != 0) {
      return "";
    }

    $guess = `cat /tmp/input.barcode`;
    system("rm -f /tmp/input.barcode");

    if (&isa_barcode($guess)) {
      $prod_barcode = &decode_barcode($guess);      
      my $selectqueryFormat = q{
        select name
        from products
        where barcode = '%s';
      };
      my $result = $conn->exec(sprintf($selectqueryFormat, $prod_barcode));
      if ($result->ntuples != 1) {
        next;
      } 
      $prodname = $result->getvalue(0,0);

      $selectqueryFormat = q{
        select phonetic_name
        from products
        where barcode = '%s';
      };
      $result = $conn->exec(sprintf($selectqueryFormat, $prod_barcode));
      if ($result->ntuples != 1) {
        next;
      } 
      $phonetic_name = $result->getvalue(0,0);

      $selectqueryFormat = q{
        select price
        from products
        where barcode = '%s';
      };
      $result = $conn->exec(sprintf($selectqueryFormat, $prod_barcode));
      if ($result->ntuples != 1) {
        system ("$DLG --title \"$prod_barcode\""
                ." --clear --msgbox"
                ." \"Product not found.  Please try again\" 9 50");
        next;
      };
      $price = $result->getvalue(0,0);

      if ($prodname eq "Done") {
        # Record all transactions at once
        &saytotal($total);
        &update_stock(@purchase);
        &update_balance($userid,$total);
        &sayit("goodbye, $username!");
        return;
      } else {
        # Update dialog
        push(@purchase, $prodname);
        push(@prices, $price);
        $numbought++;
        &sayit("$phonetic_name");
        $leng += 1;
        next;
      }

    } else {
      # do nothing
      next;
    }
  } # while(1)
}


sub
barcode_login
{
  my ($logintext) = @_;

  # Do some preprocessing first: decode and retrieve corresponding username
  $barcode = decode_barcode($logintext); 
  my $selectqueryFormat = q{
    select username 
    from users 
    where userbarcode = '%s';
  };
  my $result = $conn->exec(sprintf($selectqueryFormat, $barcode));
  if ($result->ntuples != 1) {
    # does not exist
    my $win_title = "Invalid barcode";
    my $win_text = q{
I could not find this barcode in the database. If you're 
an existing user you can change your barcode login from 
the main menu.  If you're a new user you'll need to first 
create a new account by entering a valid text login id.}; 
    system("$DLG --title \"$win_title\" --msgbox \"" .
	 $win_text .
	 "\" 10 65 2> /dev/null");
    exit 1;
  } else {
    $username = $result->getvalue(0,0);
    $userid = &bob_db_get_userid($username);
    &barcode_action_win($username,$userid,$conn);
  }
}

