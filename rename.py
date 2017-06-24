#!/usr/bin/env python3
# -*- coding: utf-8 -*-
'''rename.py

Přidat úvodní nuly
'''

import glob
import os


myfiles = glob.glob('./output/*')

for myfile in myfiles:

    no=myfile.split('/')[-1]
    no_string= "{0:0>3}".format(no)
    newname='./output/'+no_string

    os.rename(myfile,newname)


#
