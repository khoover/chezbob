#!/usr/bin/perl -w

$USAGE = "Usage: makeform.pl <template_file> <value_file>\n";

$numArgs = @ARGV;
if ($numArgs != 2) {
  print STDERR $USAGE;
  exit 1;
}

$template = $ARGV[0];
$values = $ARGV[1];

if (! -r $template) {
  print STDERR "makeform.pl: template file not readable...exiting.\n";
  exit 2;
}

if (! -r $values) {
  print STDERR "makeform.pl: values file not readable...exiting.\n";
  exit 3;
}

open(TEMPLATE, $template) ||
  die "makeform.pl: can't open template file";
$oldsep = $/;
undef $/;
$form_template = <TEMPLATE>;
$/ = $oldsep;
close(TEMPLATE);

open(VALUES, $values) ||
  die "makeform.pl: can't open values file";

$header = <VALUES>;
if (! defined $header) {
  die "nothing in values file";
}
chop($header);
@fields = split(/\s+/,$header);
$numFields = @fields;

$num = 1;

foreach $valueLine (<VALUES>) {
  chop($valueLine);
  $form = $form_template;
  @values = split(/\s+/,$valueLine);
  if (@values < $numFields) {
    $linenum = $num+1;
    print(STDERR "warning: too few fields in line $linenum\n");
  }
  if (@values > $numFields) {
    $linenum = $num+1;
    print(STDERR "warning: too many fields in line $linenum\n");
  }

  for ($i = 0 ; $i < $numFields ; $i++) {
    $f = $fields[$i];
    $v = $values[$i];
    $form =~ s/%$f%/$v/g;
  }

  open(OUT, ">$template.$num") ||
    die "makeform.pl: can't open output file $num";
  print OUT $form;
  close(OUT);
  $num++;
}

close(VALUES);
