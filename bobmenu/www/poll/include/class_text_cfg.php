<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

class text_cfg {

    var $config_file;
    var $root_dir;

    function text_cfg() {
        $this->config_file = "config.inc.php";
        $this->root_dir = ".";
    }

    function set_config_file($config_file) {
        $bad_chars = array("\\","/","*","?","\"","<",">","|");
        for ($i=0; $i<sizeof($bad_chars); $i++) {
            if (strstr($config_file, $bad_chars[$i])) {
                return false;
            }
        }
        $this->config_file = $config_file;
        return true;
    }

    function set_rootdir($cfg_dir) {
        if (!is_dir($cfg_dir)) {
            return false;
        }
        $this->root_dir = $cfg_dir;
        return true;
    }
    
    function format_array($vars_array='') {
        if (is_array($vars_array)) {
            reset($vars_array);
            if (get_magic_quotes_gpc()) {
                while (list($var, $value)=each($vars_array)) {
                    $value = stripslashes($value);
                    $value = str_replace("\"", "\\\"", $value);
                    $value = str_replace("\$", "\\\$", $value); 
                    $vars_array[$var] = trim($value);
                }
            } else {
                while (list($var, $value)=each($vars_array)) {
                    $value = str_replace("\"", "\\\"", $value);
                    $value = str_replace("\$", "\\\$", $value); 
                    $vars_array[$var] = trim($value);
                }    
            }
            reset($vars_array);
            return $vars_array;
        } else {
            return false;
        }
    }
    
    function update_cfg($array_name,$vars='') {
        if (!is_array($vars) || !eregi("^[_a-z0-9]+$", $array_name)) {
            return false;
        }   
        $vars = $this->format_array($vars);
        if (sizeof($vars)>0) {
            $config = "<?php\n";
            while (list($var,$value)=each($vars)) {
                $config .= "\$".$array_name."['".$var."'] = \"$value\";\n";
            }
            $config .= "?>";
            $fp = fopen("$this->root_dir/$this->config_file","w") or die("Unable to open $this->root_dir/$this->config_file");
            flock($fp, 2);
            fwrite($fp, $config);
            flock($fp, 3);
            fclose($fp);
            return true;
        } else {
            return false;
        }
    }


}

?>