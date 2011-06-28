
#include <stdio.h>
#include <stdlib.h>
#include "window.h" 

static int font_id   =  0 ;
static int font_size = 14 ; 
static char font_sample [] = "ABCDEFGHIJKLMNOPQRSTUVWXYZ\n"
                             "abcdefghijklmnopqrstuvwxyz\n"
                             "1234567890!@#$%^&*()_-+=~`\n"
                             "{}[]|\\:;\"'<>,.?/\n"
                             "This Program was written\n"
                             "by Steve Baker\n" ; 

Fl_Window *win ;

char *font_name[] = {
 "Helvetica", "HelveticaBold", "HelveticaItalic", "HelveticaBoldItalic",
 "Courier"  , "CourierBold"  , "CourierItalic"  , "CourierBoldItalic"  ,
 "Times"    , "TimesBold"    , "TimesItalic"    , "TimesBoldItalic"    ,
 "Symbol"   , "Terminal"     , "TerminalBold"   , "ZapfDingbats"       ,
 NULL
};

char font_title [ 256 ] ;

void exit_program(Fl_Button *, void *) { exit ( 0 ) ; }
 
void refreshSample ()
{
  fontName -> label  ( font_name[font_id] ) ;
  fontName -> redraw () ;

  sprintf ( font_title, "%s-%d [%d]", font_name[font_id], font_size, font_id );
  text_sample -> label    ( font_title  ) ;
  text_sample -> textfont ( font_id     ) ;
  text_sample -> textsize ( font_size   ) ;
  text_sample -> value    ( font_sample ) ;
  text_sample -> redraw () ;
  win -> redraw () ;
}
 
 
void setFont (Fl_Button *, void *)
{
  font_id++ ;

  if ( font_name[font_id]==NULL )
    font_id = 0 ;

  refreshSample () ;
}
 
 
void setFontSize (Fl_Value_Slider *s, void *)
{
  font_size = (int) s->value() ;  
  refreshSample () ;
}
 
 
 
int main(int argc, char **argv)
{
  win = make_window () ;  
  refreshSample () ;  
  win -> show ( argc, argv ) ;   
  Fl::run () ;
}

