#! /usr/bin/env python3
"""
counter.py -- command line data science in python


USAGE: counter.py regexp  <FILE

counter.py will match the regular expresion against every line in STDIN, and count the lines
each string matching the expression is found. The counts are output as CSV file.
Subexpressions (regular expression groups and named groups) are counted separately.
(See https://docs.python.org/3/howto/regex.html for those).

EXAMPLES

 LC_ALL=C ls ~ -l  | python3 counter.py 'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec'

will give you a stat of the months the files in your home directory were created.


 LC_ALL=C ls ~ -l  | python3 counter.py '(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec)  ?\d\d  ?(?P<year>2\d\d\d)'

will give you the stats of months and years in the named regular expression groups.


SORTING BY _SUFFIX

The stats are sorted by value - the string that was found most frequently at the top. If you want to sort
by the string found (=key) instead, append a "_k" to the name of the named group.

Example:

    cat /var/log/apache2/access.log | ./counter.py '(?P<time_k>03/Jan/2017:\d\d:)'

will give you a per-hour count of the requests logged in your webserver log on Jan. 3rd 2017, ordered by hour.
(You will need a server log at the specified location containing requests for Jan. 3rd 2017 for this to work).
You can use the suffix "_kn" if you want to sort numerically. This works by converting the strings to the python
type float first.


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


def float_or_zero(v) :
    try :
        return float(v)
    except ValueError :
        return 0.0

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
        nt=str(k).split("_")
        sorter=lambda a : a[1]
        realkey=k
        if len(nt)==2 :
            realkey=nt[0]
            if nt[1]=="k" :
                sorter=lambda a : a[0]
            elif nt[1]=="kn" :
                sorter=lambda a: float_or_zero(a[0])
            elif has_pandas and nt[1] in np.sctypeDict.keys() :
                pass
            else :
                sys.stderr.write("key suffix _{} not recognized. Possible values: _k (sort by key), _kn (sort numerically)\n".format(nt[1]))
                realkey=k
        table=sorted(list(v.items()), key=sorter ,reverse=True)
        # group name ends in _int, _float or similar: Descriptive Stats with Pandas etc.
        if has_pandas and len(nt)>1 and nt[1] in np.sctypeDict.keys() :
            if has_pandas :
                cf=getattr(np,nt[1])
                se=pd.Series([a for a in convert_or_na(table,cf)],dtype=cf, name=nt[0])
                sys.stderr.write(str(se.describe())+"\n")
        else :
        # normal behaviour
            total = 0
            for r in table :
                total += int(r[-1])
            if not firstwritten :
                f.writerow(['group','match','count','percent'])
                firstwritten=True
            for r in table :
                rr=[realkey]
                rr.extend(r)
                rr.append("%.2f%%" % ((100.0*r[-1])/total))
                f.writerow(rr)
            rr=[realkey,'total',total,'100.00%']
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

