#! /usr/bin/env python3
"""
counter.py -- command line data science in python


USAGE: counter.py [--sample] [--join=field1,field2] regexp [regexp2] [regexp3] [regexpn]  <FILE

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



JOINING COUNTERS

Normally, every named group is counted independently. You can count co-ocurrences using the --join parameter:


 LC_ALL=C ls ~ -l  | python3 counter.py --join=year,month '(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec)  ?\d\d  ?(?P<year>2\d\d\d)'

will separate November 2016 from November 2015 etc. In the first example, all the November files were counted together irrespective of the year. Rows
without matches for one value are counted as "None".


DISPLAYING SAMPLE LINES


 LC_ALL=C ls ~ -l  | python3 counter.py --sample --join=year,month '(?P<month>Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Dec)  ?\d\d  ?(?P<year>2\d\d\d)'

will add a field named "sample" to the output csv. It contains the first line that matched this counter as an example.

DESCRIPTIVE STATISTICS

If you have pandas and numpy installed, the matches of named regular expression groups with names ending in "_float" or "_int"
will be converted to the corresponding pandas Series and a series.describe() will be written to STDERR.

  printf "10 \n3 \n12 \n16 \n" | counter.py '(?P<n_float>\d+)'

will print mean, max, min, standard deviation and quartiles for the array [10, 3, 12, 16] to STDERR


This was inspired by the great O'Reilly book Data Science at the Command Line, Github Repo is here:
https://github.com/jeroenjanssens/data-science-at-the-command-line

"""
import sys
import os
import re
from collections import Counter,defaultdict,OrderedDict
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

def process(*args,join=None,sample=False) :
    rex=[]
    for rx in args :
        rex.append(re.compile(rx))
    c=defaultdict(lambda: Counter())
    if sample :
        samples=defaultdict(lambda : dict())
    for line in sys.stdin.readlines() :
        processed=set()
        valuedict=OrderedDict()
        line=line[:-1]
        for (rxc,rx) in enumerate(rex) :
            m=rx.search(line)
            if len(rex)==0 :
                rxc_key=""
            else :
                rxc_key="%d_" % (rxc+1,)
            if m :
                for (k,v) in m.groupdict().items() :
                    c[k].update({ v : 1 })
                    valuedict[k]=v
                    processed.add(v)
                    if sample and v not in samples[k]:
                        samples[k][v]=line
                for g in enumerate(m.groups()) :
                    if g[1] not in processed :
                        gkey="%s%s" % (rxc_key,g[0]+1)
                        c[gkey].update({g[1] : 1 })
                        processed.add(g[1])
                        valuedict[gkey]=g[1]
                        if sample and g[1] not in samples[gkey] :
                            samples[gkey][g[1]]=line
                if len(processed)==0 :
                    c[0].update({m.group() : 1 })
                    if sample and m.group() not in samples[0] :
                        samples[0][m.group()]=line
        if join :
            jk="join"
            jv=",".join([str(valuedict.get(a,None)) for a in join])
            c[jk].update({ jv : 1 })
            if sample and jv not in samples[jk] :
                samples[jk][jv]=line
    f=csv.writer(sys.stdout)
    firstwritten=False
    for (k,v) in c.items() :
        nt=str(k).split("_")
        sorter=lambda a : a[1]
        realkey=k
        # group name ends in _k or _kn - sort by key, sort by key numerically
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
        # group name ends in _int, _float or similar: Descriptive Stats with Pandas etc. to stderr
        if has_pandas and len(nt)>1 and nt[1] in np.sctypeDict.keys() :
            if has_pandas :
                cf=getattr(np,nt[1])
                se=pd.Series([a for a in convert_or_na(table,cf)],dtype=cf, name=nt[0])
                sys.stderr.write(str(se.describe())+"\n")
        # group name is "join" - separate joined key into columns
        if k == "join" :
            joincolumns=["join"]
            joincolumns.extend(join)
            joincolumns.append("count")
            if sample :
                joincolumns.append("sample")
            jointable=[]
            for row in table :
                trow=["join"]
                trow.extend(row[0].split(","))
                trow.append(row[1])
                if sample :
                    trow.append(samples["join"][row[0]])
                jointable.append(trow)
        else :
        # normal behaviour
            total = 0
            for r in table :
                total += int(r[-1])
            if not firstwritten :
                headers=['group','match','count','percent']
                if sample :
                    headers.append("sample")
                f.writerow(headers)
                firstwritten=True
            for r in table :
                rr=[realkey]
                rr.extend(r)
                rr.append("%.2f%%" % ((100.0*r[-1])/total))
                if sample :
                    rr.append(samples.get(realkey,defaultdict(lambda : '-'))[r[0]])
                f.writerow(rr)
            rr=[realkey,'total',total,'100.00%']
            f.writerow(rr)
    if join :
        f.writerow(joincolumns)
        for row in jointable :
            f.writerow(row)




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
        args=set(sys.argv)
        switches=set()
        join=None
        sample=False
        for a in args :
            join_test=re.match("--join=(?P<fields>[^ ]+)",a)
            if join_test :
                start=2
                join=join_test.groupdict()["fields"].split(",")
                switches.add(a)
            sample_test=re.match("--sample",a)
            if sample_test :
                sample=True
                switches.add(a)
        for s in switches :
            args.remove(s)
        process(*args,join=join,sample=sample)

