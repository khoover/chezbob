#!/bin/sh
# htmlmake.sh: Convert tab-separated data table of authors and titles into an
# html file.
# This program is released under the GNU GPL, which may be found at
# www.gnu.org. The version it is released under is the one current on the date
# June 8, 2000. Written by skiprosebaugh@email.com. Sorry that the comments are
# longer than the program.

# Usage: htmlmake.sh < datafile > books.html

# It is also possible to use this in a pipe:
# collate.py datafile1 datafile2 | htmlmake.sh > books.html
# It will likely be more useful in combination with collate.py

# If you want to make the script work like this:
# htmlmake.sh datafile > books.html
# then insert ${1} right between the sort and the | on the first line.

sort | gawk -F$'\t' 'BEGIN { OFS = "</td><td>" ; print "<html><head><title>Books I Own</title></head><body>I am slowly yet surely building up my book collection.<p><table>"} { print "<tr><td>" $1, $2 "</td></tr>" } END { print "</table></body></html>"}'

