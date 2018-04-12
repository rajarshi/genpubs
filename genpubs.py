#!/usr/bin/env python
import xml.etree.ElementTree as ET
import StringIO
import sys
import getopt
import re
import string
import urllib


def _myCap(text):
    def commonWords(x):
        if x.lower() in ['in', 'and', 'of']:
            return x.lower()
        else:
            return string.capitalize(x)
    return ' '.join(map(commonWords, text.split()))


def shortenFirstName(s):
    s = s.strip().split(',')
    last = s[0]

    # remainder
    remainder = s[1].strip()

    # see if we get a first name and initials
    first = None
    tmp = remainder.split(' ')
    if len(tmp) == 2:
        first = tmp[0][0] + '.' + tmp[1]
        if first[-1] != '.':
            first += '.'
    elif re.compile('[A-Z]\.').match(remainder):
        first = remainder
    elif re.compile('[A-Z]\.[A-Z]\.').match(remainder):
        first = remainder
    elif re.compile('[A-Z]\.[A-Z]').match(remainder):
        first = remiander + '.'
    elif len(remainder) > 4:
        first = remainder[0] + '.'
    else:
        first = remainder[0] + '.'
    return (first, last.encode('ascii', 'ignore'))


class Publication:
    def __init__(self, authorList,
                 title,
                 journal,
                 year,
                 volume,
                 number,
                 pages,
                 kwds=None,
                 url=None,
                 doi=None,
                 abstract=None):
        self.index = -1
        self.authors = authorList

        self.title = title
        self.journal = journal

        self.volume = volume
        self.number = number
        
        self.year = year
        self.pages = pages

        self.startPage = pages.split('-')[0]
        if self.startPage == '':
            self.startPage = 0
        else:
            try:
                self.startPage = int(self.startPage)
            except ValueError:  # some idiotic alphanumeric page number!
                pass

        self.abstract = abstract
        self.url = url
        self.doi = doi

        self.kwds = kwds

        self.myself = None

    def __str__(self):
        authors = ['%s, %s' % (l, f) for f, l in self.authors]
        s = """
	%s
	%s
	%s %s %s %s
	""" % (self.title,
            '; '.join(authors), self.journal,
            self.year, self.volume, self.pages)
        return s

    def setMyself(self, name):
        self.myself = name

    def getKeywords(self): return self.kwds

    def isPublished(self):
        if self.volume in ['submitted',  'in press', 'ASAP']:
            return False
        else:
            return True

    def formatJournal(self, mode='latex'):
        if self.journal is not None and self.journal != '':
            if mode == 'latex':
                return '\\textit{%s}, ' % (self.journal)
            elif mode == 'html':
                return '<i>%s</i> ' % (self.journal.replace("\&", "&"))
        else:
            return ''

    def getPaperDiv(self, id=None, show_abstract=False):
        label = ''
        doi = None

        if self.doi:
            doi = self.doi
            label = 'DOI'
        elif self.url and self.url.find('http://dx.doi.org') >= 0:
            doi = self.url.replace('http://dx.doi.org/', '')
            label = 'DOI'
        elif self.url and self.url.find('https://dx.doi.org') >= 0:
            doi = self.url.replace('https://dx.doi.org/', '')
            label = 'DOI'
        elif self.url:
            doi = self.url
            label = 'Link'

        s = StringIO.StringIO()
        s.write("<div class='paper'>\n")
        #s.write("<div class='serial'>%d</div>\n" % (id))

        if label == 'DOI':
            badge = """<span style='display:inline; float: right' class="__dimensions_badge_embed__" data-doi="%s" data-hide-zero-citations="false" data-style="small_circle"></span><script async src="https://badge.dimensions.ai/badge.js" charset="utf-8"></script>""" % (doi)
        else:
            badge = ""
        s.write("<div class='ptitle'><span class='pubindex'>%d.</span> %s %s</div>\n" %
                (self.index, self.title.replace('{', '').replace('}', ''), badge))
        s.write("<div class='pdetails'>\n")
        s.write("<div class='pauthor'>\n")

        # find the index of Guha in the author list
        authors = []
        for first, last in self.authors:
            if last.find(self.myself) != -1:
                authors.append('<span class="lead">%s, %s</span>' %
                               (last, first))
            else:
                authors.append('%s, %s' % (last, first))
        authors = '; '.join(authors)
        s.write('%s\n</div>\n' % (authors))

        if self.journal != "":
            self.journal += ","
            self.journal = self.journal.replace(",,", ",")

        if self.number != '':
            self.number = '('+self.number+')'

        if not self.isPublished():
            s.write("<div class='pjournal'>%s<b>%s</b>, %s</div>\n" %
                    (self.formatJournal('html'), self.year, self.volume))
        else:
            s.write("<div class='pjournal'>%s<b>%s</b>, <i>%s</i>%s, %s</div>\n" %
                    (self.formatJournal('html'), self.year, self.volume, self.number, self.pages))
        s.write("<div class='pmisc'>\n")
        if show_abstract:
            toggletext = '''[ <a href="javascript:toggleLayer('abstract%d');">Abstract</a> ]''' % (
                id)
        else:
            toggletext = ''
        if label == 'DOI':
            s.write("""
        %s
        [DOI <a href="%s">%s</a> ] 
        """ % (toggletext, self.url, doi))
        elif label == 'Link':
            s.write("""
        %s
        [ <a href="%s">Link</a> ]
        """ % (toggletext, self.url))
        if show_abstract:
            s.write("<div id='abstract%d' class='absdiv'>%s</div>\n\n" %
                    (id, self.abstract))
        s.write("</div>\n</div>\n</div>\n")
        return s.getvalue()


def _genLatexEntry(pub, color, id=None):
    entry = ''
    authors = []
    for first, last in pub.authors:
        if last.find(pub.myself) != -1:
            authors.append('\\textbf{%s, %s}' % (last, first))
        else:
            if color:
                authors.append(
                    '\\textcolor[rgb]{0.6, 0.6, 0.6}{%s, %s}' % (last, first))
            else:
                authors.append('%s, %s' % (last, first))
    authors = '; '.join(authors)

    # Set up URL
    if pub.url:
        labelstr = '''\\href{%s}{%d}.''' % (pub.url, id)
    else:
        labelstr = '%d.' % (id)
    labelstr = str(id) + "."

    if not pub.isPublished():
        entry = """\\entry*[%s] \\raggedright{%s; ``%s'', %s, \\textbf{%s}, %s}""" % \
            (labelstr, authors, pub.title, pub.formatJournal(
                'latex'), pub.year, pub.volume)
    else:
        entry = """\\entry*[%s] \\raggedright{%s; ``%s'', %s, \\textbf{%s}, \\textit{%s}, %s}""" % \
            (labelstr, authors, pub.title, pub.formatJournal('latex'),
             pub.year, pub.volume, pub.pages.replace('-', '--'))

    entry = entry.replace(", ,", ", ")
    return entry


def _genWikiEntry(pub):
    entry = ''
    entry += "# \"%s\"" % (pub.title) + '<br>'

    authors = []
    for first, last in pub.authors:
        authors.append('%s, %s' % (last, first))
    authors = '; '.join(authors)
    entry += authors + '<br>'

    url = pub.url
    if not url:
        url = ""
    else:
        url = urllib.unquote(url)
        url = url[:-1]
        url = '([%s DOI])' % (url)

    entry += "''%s'', '''%s''', ''%s'',  %s %s" % \
        (_myCap(pub.journal).replace("\\", ""),
         pub.year, pub.volume, pub.pages, url)
    return entry


def makeLatexPage(pubs, entrySpacer=0.7, color=False):
    s = ''

    # get total number of pubs
    npub = 0
    for pub in pubs:
        kwds = pub.getKeywords()
        if kwds and 'ignore' in kwds:
            continue
        else:
            npub += 1

    for pub in pubs:
        kwds = pub.getKeywords()
        if kwds and 'ignore' in kwds:
            print 'Ignoring: %s' % (pub.title)
            continue
        s += _genLatexEntry(pub, color, npub)
        npub = npub - 1
        s = s + '\n\\vspace{%1.1fem}\n' % (entrySpacer)
    s = '\\rubricalignment{l}\n\\begin{rubric}{Publications}\n' + \
        s + '\\end{rubric}\n'
    return s


def makeWikiPage(pubs):
    s = ''
    for pub in pubs:
        s += _genWikiEntry(pub)
        s += '\n'
    return s

def makePage(paperdiv):
    return paperdiv

def makePage2(paperdiv):
    s = """
    <html>
    <head>
        <meta http-equiv="Expires" content="0">
	<style type="text/css">  @import "../../style/paper.css"; </style>
        <style type="text/css"> @import "../../style/layout.css"; </style>
        <style type="text/css"> @import "../../style/style.css"; </style>
        <style type="text/css"> @import "../../style/writing.css"; </style>
        <script type="text/javascript" src="../../style/drop_down.js"></script>
        <script type="text/javascript" src="../../style/hideshow.js"></script>
        <title>Publications &amp; Reports</title>
    </head>
    <body class="main">

        <div id="container">
            <!--#include virtual="../../banner.html" -->
            <!--#include virtual="../../menu.html" -->
           <div id="content">

        <div class="theader">Refereed Publications</div>
        <div class="writing">

%s

</div>



           </div>

                <!--#include virtual="../../footer.html" -->
            </div>
<script src="http://www.google-analytics.com/urchin.js" type="text/javascript">
</script>
<script type="text/javascript">
  _uacct="UA-68562-2";
  urchinTracker();
</script>
    </body>
</html>
""" % (paperdiv)
    return s


def usage():
    print """
    genpubs [OPTIONS] pubs.xml

    pubs.xml should be in Endnote XML format

    -h, --help\tThis message
    -o, --out\tName of the output file
    -t, --type\tType of output. Can be 'latex' or 'html' or 'wiki'
    -c, --color\tIf specified, author names are dimmed
    -m, --myself\tIf specified, your own last name (for highlighting)
    """


if __name__ == '__main__':
    pubtype = 'html'
    pubsout = 'pubs.txt'
    color = False
    forcejournal = True
    showabs = False
    myself = 'Guha'

    if len(sys.argv) == 1:
        usage()
        sys.exit(-1)

    try:
        opt, args = getopt.getopt(sys.argv[1:], 'o:t:m:hcja',
                                  ['out=', 'type=', 'help', 'color', 'forcejournal', 'abstract', 'myself'])
    except getopt.GetoptError:
        usage()
        sys.exit(-1)

    for o, a in opt:
        if o in ('-c', '--color'):
            color = True
        elif o in ('-j', '--journal'):
            forcejournal = True
        elif o in ('-h', '--help'):
            usage()
            sys.exit(1)
        elif o in ('-o', '--out'):
            pubsout = a
        elif o in ('-m', '--myself'):
            myself = a
        elif o in ('-a', '--abstract'):
            showabs = True
        elif o in ('-t', '--type'):
            pubtype = a
            if pubtype not in ['latex', 'html', 'wiki']:
                usage()
                sys.exit(-1)

    pubsin = sys.argv[-1]
    try:
        f = open(pubsin, 'r')
        f.close()
    except IOError:
        print "\nError opening specified bibligraphy: %s" % (pubsin)
        usage()
        sys.exit(-1)

    pubs = []

    tree = ET.parse(pubsin)
    records = tree.getroot().find('records')
    n = 0
    for record in records.findall('record'):
        authors = record.findall('contributors/authors/author')
        authors = [shortenFirstName(x) for x in [x.text for x in authors]]
        title = record.findall('titles/title')[0].text
        custom3 = record.findall('custom3')[0].text
        if custom3 != 'article':
            continue

        journal = record.findall('titles/secondary-title')
        if not journal and not forcejournal:
            sys.stderr.write("ERROR: '%s' had no journal - skipped\n" % (title))
            continue
        elif not journal and forcejournal:
            journal = ""
        else:
            journal = journal[0].text

        journal = journal.replace('~', ' ')

        volume = record.findall('volume')
        if not volume:
            volume = '' #continue
        else:
            volume = volume[0].text

        number = record.findall('number')
        if not number:
            number = '' #continue
        else:
            number = number[0].text

        year = record.findall('dates/year')[0].text
        pages = record.findall('pages')
        if not pages:
            pages = ''
        else:
            pages = pages[0].text
        pages = pages.replace('--', '-')

        url = record.findall('urls/related-urls/url')
        if not url:
            url = ''
        else:
            url = url[0].text

        doi = record.findall('electronic-resource-num')
        if not doi:
            doi = ''
        else:
            doi = doi[0].text

        abstract = record.findall('abstract')
        if not abstract:
            abstract = ''
        else:
            abstract = abstract[0].text
        kwds = record.findall('keywords/keyword')
        if not kwds:
            kwds = None
        elif kwds[0].text == None:
            kwds = None
        else:
            kwds = [x.strip() for x in kwds[0].text.split(';')]
        title = title.encode('ascii', 'ignore')
        p = Publication(authors, title, journal, year,
                        volume, number, pages, kwds, url, doi, abstract)
        p.setMyself(myself)
        pubs.append(p)

    pubs.sort(lambda x, y:  cmp((x.year, x.volume, x.startPage),
                                (y.year, y.volume, y.startPage)))
    pubs.reverse()
    for i in range(0, len(pubs)):
        pubs[i].index = len(pubs) - i
    print '%d publications [article]' % (len(pubs))
    o = open(pubsout, 'w')
    if pubtype == 'html':
        s = "\n\n<div class='pspacer'></div>\n\n"
        c = 1
        for p in pubs:
            s += p.getPaperDiv(c, show_abstract=showabs) + \
                "\n\n<div class='pspacer'></div>\n\n"
            c += 1

        try:
            s = s.encode('ascii', 'replace')
            o.write(makePage(s))
        except:
            sys.exit(-1)
    elif pubtype == 'latex':
        o.write(makeLatexPage(pubs, color=color).encode('ascii', 'ignore'))
    elif pubtype == 'wiki':
        o.write(makeWikiPage(pubs))

    o.close()
