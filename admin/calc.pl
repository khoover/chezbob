#!/usr/bin/perl -w

sub Usage {
  print STDERR "Usage: calc.pl <price_list> [<item_list>]\n";
  exit();
}


sub parsePrices {
  foreach (@_) {
    chop;

    @priceline = split;
    $numElts = @priceline;
    if ($numElts != 3) {
      printf STDERR "warning: price line does not parse: $_\n";
      next;
    }

    ($i,$p,$t) = @priceline;

    if (defined $hash{$i}) {
      printf STDERR "warning: price for item $i duplicately defined\n";
      next;
    }

    $hash{$i} = "$p:$t";
  }

  %hash;
}



###
### don't like how $#ARGV behaves...
###
$numArgs = @ARGV;

if ($numArgs > 2 || $numArgs < 1) {
  Usage();
}

open(PRICES, $ARGV[0]) || die "error opening price list \"$ARGV[0]\"\n";

@lines = <PRICES>;
%priceHash = parsePrices(@lines);

#print %priceHash;
close(PRICES);

if ($numArgs == 2) {
  open(ITEMS, $ARGV[1]) || die "error opening items list \"$ARGV[1]\"\n";
  @lines = <ITEMS>;
}
else {
  @lines = <STDIN>;
}

$total = 0;
$totaltax = 0;
@unknownItems = ();
foreach (@lines) {
  chop;

  @itemline = split;
  $numElts = @itemline;
  if ($numElts != 2) {
    printf STDERR "warning: item line does not parse: $_\n";
    next;
  }

  ($item,$qty) = @itemline;

  if (! defined $priceHash{$item}) {
    printf STDERR "warning: unknown item: $item\n";
    push(@unknownItems, $item);
    next;
  }

  ($itemprice,$itemtaxable) = split(/:/,$priceHash{$item});

  $extendedprice = $qty * $itemprice;
  printf("%d @ \$%.2f = ", $qty, $itemprice);
  if ($itemtaxable eq "y" || $itemtaxable eq "Y") {
    $tax = $extendedprice * 0.0775;

    printf("\$%.2f + \$%.2f = \$%.2f\n",
	   $extendedprice, $tax, $extendedprice+$tax);
    $total += $extendedprice + $tax;
    $totaltax += $tax;
  }
  else {
    printf("\$%.2f\n", $extendedprice);
    $total += $extendedprice;
  }
}

printf("total bill is \$%.2f (subtotal = \$%.2f, tax = \$%.2f)\n",
       $total, $total-$totaltax, $totaltax);

$numUnknown = @unknownItems;
for ($i = 0 ; $i < $numUnknown ; $i++) {
  printf("  >>> unknown item: $unknownItems[$i]\n");
}
