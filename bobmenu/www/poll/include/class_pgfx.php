<?php
/**
 * ----------------------------------------------
 * Advanced Poll 2.0.2 (PHP)
 * Copyright (c)2001 Chi Kien Uong
 * URL: http://www.proxy2.de
 * ----------------------------------------------
 */

class pgfx extends poll {

    var $colors = array();
    var $begin = 0;

    function pgfx() {
        $this->poll();
        $this->colors = array(
            "aqua"      => "145,187,234",
            "blue"      => "73,96,214",
            "brown"     => "176,112,86",
            "darkgreen" => "18,117,53",
            "gold"      => "220,170,75",
            "green"     => "30,191,56",
            "grey"      => "207,188,192",
            "orange"    => "240,131,77",
            "pink"      => "244,109,188",
            "purple"    => "149,57,214",
            "red"       => "205,31,119",
            "yellow"    => "240,213,67",
            "blank"     => "255,255,255",
            "black"     => "0,0,0"
        );        
    }

    function output_png($poll_id,$radius) {
        if ($radius < 20) {
            $radius = 90;
        }
        $diameter = $radius*2;
        $img_size = $diameter+2;
        if ($this->is_valid_poll_id($poll_id)) {
            $img = ImageCreate($img_size, $img_size);
            for(reset($this->colors); $key=key($this->colors); next($this->colors)) {
                eval("\$poll_colors[\$key]=ImageColorAllocate(\$img,".$this->colors[$key].");");
            }
            ImageFill($img,0,0,$poll_colors['blank']);            
            Imagearc($img,$radius,$radius,$diameter,$diameter,0,360,$poll_colors['black']);
            if (!isset($this->options[$poll_id])) {
                $this->get_poll_data($poll_id);
            }
            if (count($this->poll_array)) {                
                if ($this->pollvars['result_order'] == "asc") {
                    uasort($this->poll_array,"sort_poll");
                } elseif ($this->pollvars['result_order'] == "desc") {
                    uasort($this->poll_array,"rsort_poll");
                }
            }
            $totalvotes = ($this->total_votes<=0) ? 1 : $this->total_votes;
            for (reset($this->poll_array); $key=key($this->poll_array); next($this->poll_array)) {
                $img_width = ($this->poll_array[$key]*360)/$totalvotes;
                $end = $this->begin + $img_width;
                $y1 = sin($end/180*M_PI)*$radius;
                $x1 = cos($end/180*M_PI)*$radius;
                Imageline($img, $radius, $radius, $radius+$x1, $radius+$y1, $poll_colors['black']);
                $end2 = $this->begin + $img_width*0.5;        
                $x2 = (int) ($radius+cos($end2/180*M_PI)*15);
                $y2 = (int) ($radius+sin($end2/180*M_PI)*15);
                Imagefilltoborder($img,$x2,$y2, $poll_colors['black'], $poll_colors[$this->color_array[$key]]);
                $this->begin += $img_width;
            }
            $this->begin = 0;
            ImageColorTransparent($img,$poll_colors['blank']);
            ImagePNG($img);
        } else {
            $loc = "$pollvars[base_url]/image/error.png";
            header("Location: $loc");
            exit();
        }
    }
    
}

?>