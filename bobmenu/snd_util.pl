

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

