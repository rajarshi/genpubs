# Generate formatted publication list from Endnote XML

A simple Python script to convert a list of publications in [Endnote XML](https://gist.github.com/low-decarie/3831049) format into HTML or LaTeX formats. I use [BibDesk](http://bibdesk.sourceforge.net/) to manage my publication list, and it supports Endnote XML format as an o utput format.

The HTML output generated by this script employs some custom [CSS](http://blog.rguha.net/wp-content/themes/hellish-simplicity/custom-css/style-1109.css) ([example](https://gist.github.com/low-decarie/3831049)). The LaTeX generates output that assumes you're using the publication list in a CV built using the [CuRve](https://www.ctan.org/pkg/curve) package. See the _Publications_ section in my [CV](http://www.rguha.net/cv.pdf).

Example usage is 
```
./genpubs.py -t html -o pubs.html pubs.xml
```

