#!/usr/bin/env python
import sys,os
import sqlite3
import argparse
from MMlib import bash

parser = argparse.ArgumentParser(description='Generate a db for ncbi_taxonomy_tree.py. With no arguments, the program downloads the current "taxdump" from ncbi taxonomy and generates the tax.bd in the current directory')
parser.add_argument("-f","--folder",  help="folder containing names.dmp and nodes.dmp files from ncbi. tax.db will be created there")
args = parser.parse_args()

if not args.folder:
    sys.stderr('Downloading taxdump.tar.gz...')
    b = bash('wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz')
    if b[0]: raise Exception, b[1]
    b = bash('wget ftp://ftp.ncbi.nih.gov/pub/taxonomy/taxdump.tar.gz.md5')
    if b[0]: raise Exception, b[1]
    md5 = [ x.rstrip() for x in open('taxdump.tar.gz.md5') ][0]
    b = bash('md5sum taxdump.tar.gz')
    if b[0]: raise Exception, b[1]
    if not md5 == b[1]:
        raise Exception, "ERROR: something went wrong with wget, md5sums do not match: %s != %s" % (md5,b[1])
    b=bash('gunzip -c taxdump.tar.gz | tar xf -')
    if b[0]: raise Exception, b[1]
    args.folder = '.'
    sys.stderr('DONE!\n')


args.folder = args.folder.rstrip('/') +'/'

names_dict = {}
for i in open(args.folder + 'names.dmp'):
    tax_id, name_txt, unique_name, name_class = i.rstrip('\t|\n').split('\t|\t')
    names_dict.setdefault(tax_id, {}).setdefault(name_class, name_txt)

nodes_dict = {}
for i in open(args.folder +'nodes.dmp'):
    tax_id, parent_tax_id, rank= i.split('\t|\t')[:3]
    nodes_dict.setdefault(tax_id, {}).setdefault('parent_tax_id', parent_tax_id)
    nodes_dict.setdefault(tax_id, {}).setdefault('rank', rank)

sys.stderr.write("I'm going to insert %s taxids into tax.db, this may take a while\n" % len(nodes_dict))
con = sqlite3.connect(args.folder + 'tax.db')
with con:
    cur = con.cursor()    
    cur.execute("DROP TABLE IF EXISTS species")
    cur.execute("CREATE TABLE species (taxid INT PRIMARY KEY, parent INT, rank VARCHAR(50), name VARCHAR(50))")

    sys.stderr.write( 'INSERTING...' )
    for taxid in nodes_dict:
        parent = nodes_dict[ taxid ][ 'parent_tax_id' ]
        rank   = nodes_dict[ taxid ][ 'rank' ]
        name   = names_dict[ taxid ][ 'scientific name' ]
        cur.execute('INSERT INTO species VALUES('+ taxid +', '+ parent +', "'+ rank +'", "'+ name +'")')

    sys.stderr.write( 'DONE!\n' )


