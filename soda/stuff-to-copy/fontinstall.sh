#!/bin/sh

[ -e /usr/share/fonts/truetype/sodafonts/lcars.ttf ] || {
	mkdir -p /usr/share/fonts/truetype/sodafonts
	cp lcars.ttf /usr/share/fonts/truetype/sodafonts/
	defoma-hints -c --no-question truetype /usr/share/fonts/truetype/sodafonts/lcars.ttf > lcars.hints
	defoma-font register-all lcars.hints
	defoma-reconfigure
}
