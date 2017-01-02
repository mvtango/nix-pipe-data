#! /usr/bin/env python3
"""
counter.py -- command line data science in python


USAGE: counter.py regexp  <FILE

counter.py will match the regular expresion against every line in STDIN, count the time
the expression and each subexpression is matched and output the counts into as CSV file.
Subexpressions are regular expression groups and named groups as defined
in https://docs.python.org/3/howto/regex.html.

EXAMPLES

 LC_ALL=C ls ~ -l  | counter.py 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec'

will give you a stat of the months the files in your home directory were created.


 LC_ALL=C ls ~ -l  | counter.py '(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec)  ?\d\d  ?(?P<year>2\d\d\d)'

will give you the stat of months and years.


This was inspired by the great O'Reilly book Data Science at the Command Line, Github Repo is here:
https://github.com/jeroenjanssens/data-science-at-the-command-line

"""
import sys
import os
import re
from collections import Counter,defaultdict
import csv


def process(ex) :
    rex=re.compile(ex)
    c=defaultdict(lambda: Counter())
    for line in sys.stdin.readlines() :
        m=rex.search(line)
        processed=set()
        if m :
            for (k,v) in m.groupdict().items() :
                c[k].update({ v : 1 })
                processed.add(v)
            for g in enumerate(m.groups()) :
                if g[1] not in processed :
                    c[g[0]+1].update({g[1] : 1 })
                    processed.add(g[1])
            if len(processed)==0 :
                c[0].update({m.group() : 1 })
    f=csv.writer(sys.stdout)
    f.writerow(['group','match','count','percent'])
    for (k,v) in c.items() :
        table=sorted(list(v.items()), key=lambda a: a[1],reverse=True)
        total = 0
        for r in table :
            total += int(r[-1])
        for r in table :
            rr=[k]
            rr.extend(r)
            rr.append("%.2f%%" % ((100.0*r[-1])/total))
            f.writerow(rr)
        rr=[k,'total',total,'100.00%']
        f.writerow(rr)


if __name__=='__main__' :
    if len(sys.argv)<2 :
        print(__doc__)
    else :
        process(sys.argv[1])

