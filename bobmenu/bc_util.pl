# bc_util.pl
#
# This file contains a set of barcode utilities.  Some are specific to the 
# Cuecat scanner.  The Cuecat is unique in that it does not output plain
# ascii, but an encoded stream.  'decode_cuecat_barcode' is a utility that
# can extract the barcode from the encoded stream.  Refer to 
# http://oss.lineo.com/cuecat/ for more information on Cuecat's.
#
# We are currently using a Metrologic MS951-47 barcode scanner 
# (http://www.metrologic.com/corporate/products/pos/MS900.htm) that was
# purchased from Ebay for $105 (Note: the website also contains pdf versions
# of the manuals which are crucial for programming the scanner).  This
# particular scanner was chosen for 2 reasons: first, it uses a simple
# keyboard (ps/2) interface and therefore doesn't require any special
# software.  Secondly, it's triggerless; it uses an infrared sensor to 
# detect when an object is nearby, and then activate the laser.
#
# Interestingly, we can exploit the encoded stream of the Cuecat to 
# determine whether we're dealing with barcode or keyboard input (well, 
# unless the user is crazy enough to enter the encoded barcode in by hand).
# The Metrologic doesn't have this property and it's much more difficult
# to distinguish between the two.  The current Bob code doesn't try to 
# make any distinction.
#
# Refer to http://www.adams1.com/pub/russadam/upccode.html for general 
# information on barcode standards.
#
# Michael Copenhafer (mcopenha@cs.ucsd.edu)
# Wesley Leong (wleong@cs.ucsd.edu)
# Created: 5/12/00
#
# $Id: bc_util.pl,v 1.4 2001-05-14 06:47:33 mcopenha Exp $
#

sub
preprocess_barcode
#
# If it's a cuecat barcode then decode it; otherwise just return orig. str
#
{
  my ($barcode) = @_;
  if (&isa_cuecat_barcode($barcode)) {
    return (&decode_cuecat_barcode($barcode));
  } else {
    return ($barcode);
  }
}


sub
isa_barcode
{
  my ($str) = @_;
  return (&isa_cuecat_barcode($str) || 
          &isa_regular_barcode($str));
}


sub
isa_regular_barcode
#
# Return 1 if input begins with a number; return 0 otherwise
#
{
  my ($barcode) = @_;
  return ($barcode =~ /^[0-9]/);
}


sub
isa_upc_barcode
#
# There are two types of UPC barcodes: UPC version A symbols have 10 digits 
# plus two overhead digits; UPC version E has 6 digits plus two overhead 
# digits. Both the metrologic and cuecat scanners retrieve all 12 digits of
# type A barcodes.  The cuecat scanner retrieves all 6 digits of the type E
# barcodes plus the last digit of overhead, but misses the first overhead
# digit.  The metrologic misses both overhead digits when scanning type E.
# 
{
  my ($barcode) = @_;
  my $leng = length($barcode);
  my $type_E_leng = 6;
  if (&isa_cuecat_barcode($barcode)) {
    $type_E_leng = 7;
  } 

  return (($leng == 12 || $leng == $type_E_leng)
          && ($barcode !~ /[^0-9]+/));
}

#---------------------------------------------------------------------------
# Cuecat utils

sub
isa_cuecat_barcode
#
# Cuecat headers begin with '.C' and contain 3 fields -- one for the header,
# one for the barcode type, and one for the barcode data.  Perl returns
# one empty token so we look for 4.
#
{
  my ($rawInput) = @_;
  if ($rawInput =~ /^\.C/) {
    my @getParsed = split /\./,$rawInput;
    my $numToken = @getParsed;
    if ($numToken == 4) {
        return 1;
    }
  }
  return 0;
}


sub
decode_cuecat_barcode
#
# Larry Wall's amazing hack to decode cuecat headers adapted by Wesley
#
{
  my ($rawInput) = @_;
  my @getParsed = split /\./,$rawInput;
  my $rawBarcode = $getParsed[3];
  $rawBarcode =~ tr/a-zA-Z0-9+-/ -_/;
  $rawBarcode = unpack 'u', chr(32 + length($rawBarcode) * 3/4)
      . $rawBarcode;
  $rawBarcode =~ s/\0+$//;
  $rawBarcode ^= "C" x length($rawBarcode);
  return $rawBarcode;
}


