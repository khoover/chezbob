<?php
function easyRead($filename)
{
  $text = "";
  $fd = fopen($filename, "r");
  while (!feof($fd)){
    $buffer = fgets($fd, 4096);
    $text = $text.$buffer;
  }
  return $text;
}

function easyWrite($filename, $input )
{
    $file = fopen($filename, "w");
    fwrite( $file, $input );
}
?>
