<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

class poll_template {

    var $root_dir;
    var $vars = array();
    var $files = array();
    var $start = '{';
    var $end = '}';
    var $pre_output = array();
    var $html_output = array();
    
    function poll_template() {
        $root_dir = ".";
    }

    function set_rootdir($tpl_dir) {
        if (!is_dir($tpl_dir)) {
            return false;
        }
        $this->root_dir = $tpl_dir;
        return true;
    }

    function set_identifiers($start, $end) {
        $this->start = $start;
        $this->end = $end;
        return true;
    }

    function clear_vars() {
        $this->files = '';
        $this->vars = '';
        return true;
    }

    function register_vars($filename, $vars) {
        if (is_array($vars)) {
            reset ($vars);
            while (list($name, $value) = each($vars)) {
                $this->vars[$filename][$name] = $value;
            }
            return true;
        } else {
            return false;
        }
    }

    function set_templatefiles($filename_array) {
        if (!is_array($filename_array)) {
            return 0;
        }
        $valid = 0;
        reset($filename_array);
        while(list($filename, $file_path) = each($filename_array)) {
            if (substr($filename, 0, 1) != '/') {
                $file_path = $this->root_dir . '/' . $file_path;
            }
            if (file_exists($file_path)) {
                $fp = fopen($file_path, 'r');                
                $this->files[$filename] = fread($fp, filesize($file_path));
                fclose($fp);
                $valid ++;
            }
        }
        return $valid;
    }

    function pre_parse($filename) {
        if (isset($this->pre_output[$filename]) && !empty($this->pre_output[$filename])) {
            return $this->pre_output[$filename];
        }
        if (isset($this->vars[$filename])) {
            reset($this->vars[$filename]);
            $this->pre_output[$filename] = ereg_replace("\"", "\\\"", $this->files[$filename]);
            while(list($name, $value) = each($this->vars[$filename])) {
                $value = ereg_replace("\"", "\\\"", $value);
                $this->pre_output[$filename] = str_replace($this->start.$name.$this->end, $value, $this->pre_output[$filename]);
            }
        } else {
            $this->pre_output[$filename] = ereg_replace("\"", "\\\"", $this->files[$filename]);
        }
        return $this->pre_output[$filename];
    }
    
    function parse($filename) {
        if (isset($this->html_output[$filename]) && !empty($this->html_output[$filename])) {
            return $this->html_output[$filename];
        }
        if (isset($this->vars[$filename])) {
            reset($this->vars[$filename]);
            while(list($name, $value) = each($this->vars[$filename])) {
                $this->html_output[$filename] = str_replace($this->start.$name.$this->end, $value, $this->html_output[$filename]);
            }
        } else {
            return $this->files[$filename];
        }
        return $this->html_output[$filename];
    }
}

?>