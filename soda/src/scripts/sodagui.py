#!/usr/bin/python

# IN PROGRESS
# export PYTHONPATH=`pwd`/../lib

from pybob.pysodaui.app import SodaApp

app = SodaApp(0, unique=False)
app.MainLoop()
app.Exit()
