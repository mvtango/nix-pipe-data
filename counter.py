#! /usr/bin/env python3
"""
counter.py -- command line data science in python


USAGE: counter.py regexp  <FILE

counter.py will match the regular expresion against every line in STDIN, count the time
each variant of the expression is matched and output the counts as CSV file.
Subexpressions (regular expression groups and named groups) are treated the same way.
(See https://docs.python.org/3/howto/regex.html for those).

EXAMPLES

 LC_ALL=C ls ~ -l  | python3 counter.py 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec'

will give you a stat of the months the files in your home directory were created.


 LC_ALL=C ls ~ -l  | python3 counter.py '(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec)  ?\d\d  ?(?P<year>2\d\d\d)'

will give you the stat of months and years in the named regular expression groups.


DESCRIPTIVE STATISTICS

If you have pandas and numpy installed, the matches of named regular expression groups with names ending in "_float" or "_int"
will be converted to the corresponding pandas Series and a series.describe() will be written to STDERR.

  printf "10 \n3 \n12 \n16 \n" | counter.py '(?P<n_float>\d+)'

will print mean, max, min, standard deviation and quartiles for the array [10, 3, 12, 16].


This was inspired by the great O'Reilly book Data Science at the Command Line, Github Repo is here:
https://github.com/jeroenjanssens/data-science-at-the-command-line

"""
import sys
import os
import re
from collections import Counter,defaultdict
import csv

try :
    import pandas as pd
    import numpy as np
    has_pandas=True
except ImportError :
    has_pandas=False


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
    firstwritten=False
    for (k,v) in c.items() :
        table=sorted(list(v.items()), key=lambda a: a[1],reverse=True)
        nt=str(k).split("_")
        # group name ends in _int, _float or similar: Descriptive Stats with Pandas etc.
        if len(nt)>1 and nt[1] in np.sctypeDict.keys() :
            if has_pandas :
                cf=getattr(np,nt[1])
                se=pd.Series([a for a in convert_or_na(table,cf)],dtype=cf, name=nt[0])
                sys.stderr.write(str(se.describe())+"\n")
            else :
                sys.stderr.write("Can't write descriptive stats for {}. Please install pandas and numpy.".format(k))
        else :
        # normal behaviour
            total = 0
            for r in table :
                total += int(r[-1])
            if not firstwritten :
                f.writerow(['group','match','count','percent'])
                firstwritten=True
            for r in table :
                rr=[k]
                rr.extend(r)
                rr.append("%.2f%%" % ((100.0*r[-1])/total))
                f.writerow(rr)
            rr=[k,'total',total,'100.00%']
            f.writerow(rr)



def convert_or_na(table,conv) :
    try :
        nanv=conv(np.NaN)
    except ValueError :
        # no integer NaN :-(
        nanv=None
    for r in table :
        try :
            v=conv(r[-2])
        except Exception as e:
            v=nanv
        if v is not None :
            for t in range(0,r[-1]) :
                yield v


if __name__=='__main__' :
    if len(sys.argv)<2 :
        print(__doc__)
    else :
        process(sys.argv[1])

