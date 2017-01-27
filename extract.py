#! /usr/bin/env python3
"""
extract.py -- command line log file processor


USAGE: extract.py regexp1 regexp2 regexp3  <FILE

will generate a CSV with header with the matches (or None if no match) for each regexp as fields. If the regexp contain
a named group, the name of this group will be used as the header for the column.


Inspired by [RegExSerDe](https://github.com/apache/hive/blob/trunk/contrib/src/java/org/apache/hadoop/hive/contrib/serde2/RegexSerDe.java).

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


maxbuffer=10000



def process(argl) :
    buff=OrderedDict()
    rex=[re.compile(a) for a in argl]
    w=csv.writer(sys.stdout)
    headerrow=[]
    headerwritten=False
    for line in sys.stdin.readlines() :
        row=[]
        for i,r in enumerate(rex) :
            m=r.search(line)
            if m :
                if m.groupdict() :
                    row.append(list(m.groupdict().values())[0])
                else :
                    row.append(m.groups()[0])
            else :
                row.append(None)
            if not headerwritten :
                if m.groupdict() :
                    headerrow.append(list(m.groupdict().keys())[0])
                else :
                    headerrow.append("f%s" % i)
        if not headerwritten :
            w.writerow(headerrow)
            headerwritten=True
        w.writerow(row)


if __name__=='__main__' :
    if len(sys.argv)<2 :
        print(__doc__)
    else :
        process(sys.argv[1:])

