#!/usr/bin/python

# shelve.py: Look up ISBN numbers in various Web databases
# This program is in the public domain.

# Written by Andrew Plotkin (erkyrath@eblong.com)
# http://www.eblong.com/zarf/bookscan/

import sys
import types
import time
import string
import fileinput
import re
import urllib

def percentthunk(match):
    hexnum = match.group(1)
    retval = chr(string.atoi(hexnum, 16))
    return retval

class GetDummy:
    name = 'Dummy'
    def makeurl(dummy, isbn):
        return ''
    def extract(dummy, buf):
        return 'dummy says no'

killtags = re.compile('<.*?>', re.DOTALL)
sanewhite = re.compile('[ \012\015\011]+')
#valtabchap = re.compile('<!--Book Items start-->')
valtabchap = re.compile('<FONT[^>]*SIZE=3>')
#boldexchap = re.compile('<B>.*?</B>', re.DOTALL)
boldexchap = re.compile('.*?</FONT>', re.DOTALL)
authexchap = re.compile('<A[^>]*AuthorRedirect[^>]*>')
namexchap = re.compile('q1=([^&]*)&q2=([^&"]*)')
killplus = re.compile('\\+')
killpercent = re.compile('%([0-9a-fA-F][0-9a-fA-F])')
anylowercase = re.compile('[a-z]')

class GetChapters:
    name = 'Chapters'
    def makeurl(dummy, isbn):
        return ('http://www.chapters.ca/books/details/default.asp?ISBN='
            + isbn)
    def extract(dummy, buf):
        fres = valtabchap.search(buf)
        if (fres == None):
            return 'Not found'
        buf2 = buf[fres.end() : ]
        titleres = boldexchap.search(buf2)
        title = killtags.sub('', titleres.group())
        title = string.strip(title)
        author = ''
        flist = authexchap.findall(buf2)
        for fres in flist:
            authres2 = namexchap.search(fres)
            if (len(author) != 0):
                author = author + '; '
            auth2 = killplus.sub(' ', authres2.group(2))
            auth1 = killplus.sub(' ', authres2.group(1))
            auth2 = killpercent.sub(percentthunk, auth2)
            auth1 = killpercent.sub(percentthunk, auth1)
            auth3 = string.strip(auth2) + ', ' + string.strip(auth1)
            if (anylowercase.search(auth3) == None):
                auth3 = string.capwords(auth3)
            author = author + auth3
        title = sanewhite.sub(' ', title)
        author = sanewhite.sub(' ', author)
        return (author, title)

valform = re.compile('<form.*handle-buy')
valformend = re.compile('</form')
#strongex = re.compile('<strong>.*?</strong>', re.DOTALL)
#authorex = re.compile('/Author=([^/"]*)')
strongex = re.compile('<b><font face=verdana,arial,helvetica>.*?</font></b>')
authorex = re.compile('&field-author=([^/"]*)')

class GetAmazon:
    name = 'Amazon'
    def makeurl(dummy, isbn):
        return 'http://www.amazon.com/exec/obidos/ISBN=' + isbn + '/'
    def extract(dummy, buf):
        fres = valform.search(buf)
        if (fres == None):
            return 'Not found'
        buf2 = buf[fres.start() : ]
        fres = valformend.search(buf2)
        buf3 = buf2[0 : fres.start()]
        titleres = strongex.search(buf3)
        title = killtags.sub('', titleres.group())
        flist = authorex.findall(buf3)
        author = ''
        for fres in flist:
            res = killpercent.sub(percentthunk, fres)
            if (len(author) != 0):
                author = author + '; '
            author = author + res
        title = sanewhite.sub(' ', title)
        author = sanewhite.sub(' ', author)
        return (author, title)

#authorexuk = re.compile('/Author=([^/"]*)')
authorexuk = re.compile('&field-author=([^/"]*)')
#valsegauk = re.compile('<font size=\\+1>')
valsegauk = re.compile('<b>')
valendauk = re.compile('<table')
#boldexauk = re.compile('<b>.*?</b>', re.DOTALL)
boldexauk = re.compile('<b>.*?<br>', re.DOTALL)

class GetAmazonUK:
    name = 'AmazonUK'
    def makeurl(dummy, isbn):
        return 'http://www.amazon.co.uk/exec/obidos/ASIN/' + isbn + '/'
    def extract(dummy, buf):
        if (string.find(buf, 'Amazon.co.uk Error Page') >= 0):
            return 'Not found'
        fres = valsegauk.search(buf)
        if (fres == None):
            return 'Not found'
        buf2 = buf[fres.start() : ]
        fres = valendauk.search(buf2)
        buf3 = buf2[0 : fres.start()]
        titleres = boldexauk.search(buf3)
        title = killtags.sub('', titleres.group())
        flist = authorexuk.findall(buf3)
        author = ''
        for fres in flist:
            res = killpercent.sub(percentthunk, fres)
            if (len(author) != 0):
                author = author + '; '
            author = author + res
        title = sanewhite.sub(' ', title)
        author = sanewhite.sub(' ', author)
        return (author, title)

searchlist = [ GetAmazon, GetChapters, GetAmazonUK ]

for line in fileinput.input():
    time.sleep(1)
    line = string.strip(line)
    if (len(line) == 0):
        continue
    comment = ''
    commentpos = string.find(line, '#')
    if (commentpos >= 0):
        comment = line[commentpos:]
        line = line[0:commentpos]
        line = string.strip(line)
    if (len(line) == 0):
        sys.stdout.write(comment + '\n')
        continue
    if (len(line) != 10):
        sys.stdout.write('# ' + line + ' # Not an ISBN' + comment + '\n')
        continue
    gotit = 0
    for cla in searchlist:
        target = cla()
        sys.stderr.write('Querying ' + target.name + ' for ISBN ' + 
            line + '...\n')
        url = target.makeurl(line)
        try:
            infl = urllib.urlopen(url)
            html = infl.read()
            infl.close()
            res = target.extract(html)
            if (type(res) != types.StringType):
                gotit = 1
                if (len(res[0])):
                    sys.stdout.write(res[0])
                else:
                    sys.stdout.write('-')
                sys.stdout.write('\t')
                if (len(res[1])):
                    sys.stdout.write(res[1])
                else:
                    sys.stdout.write('-')
                sys.stdout.write('\n')
        except:
            res = sys.exc_info()
            res = str(res[1])
        sys.stderr.write('...' + str(res) + '\n')
        if (gotit):
            break
    if (not gotit):
        sys.stdout.write('# ' + line + ' # ' + res + comment + '\n')

