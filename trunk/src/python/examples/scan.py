#!/usr/bin/env python

from gumbi import Info, ScanBus

i = Info()
print i.Info()
i.Close()

s = ScanBus()
print "I/O count:", s.Scan()
s.Close()
