all:


install:
	echo "This set of commands to run was written as being tested, so there may be slight issues; fix them as you go"
	cp xinitrc /home/kiosk/.xinitrc
	chown kiosk /home/kiosk/.xinitrc
	chmod 755 /home/kiosk/.xinitrc
	cp autox /etc/init.d/autox
	chmod 755 /etc/init.d/autox
	./fontinstall.sh
