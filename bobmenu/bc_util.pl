

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


