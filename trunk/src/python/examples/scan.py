#!/usr/bin/env python

from gumbi import Info, ScanBus

s = ScanBus()
s.Scan()
s.Close()

i = Info()
print i.Info()
i.Close()
