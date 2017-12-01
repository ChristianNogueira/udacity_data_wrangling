#!/usr/bin/env python
# -*- coding: utf-8 -*-

import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow
from bs4 import BeautifulSoup
import sys

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file) 

OSM_FILE = "C:\\Users\\christian\\Documents\\udacity\\data_wrangling\\data\\sao-paulo_moema.osm"  # Replace this with your osm file
SAMPLE_FILE = "C:\\Users\\christian\\Documents\\udacity\\data_wrangling\\data\\sao-paulo_moema_small.osm"

def get_element(osm_file, tags=('node', 'way', 'relation')):
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def resize_map():
    k = 20 # Parameter: take every k-th top level element
    with open(SAMPLE_FILE, 'wb') as output:
        output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write(b'<osm>\n  ')
    
        # Write every kth top level element
        for i, element in enumerate(get_element(OSM_FILE)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))
    
        output.write(b'</osm>')

def analise(file_name):
    
    with open(file_name, "r", encoding="utf-8") as xml:
        soup = BeautifulSoup(xml, "xml")
        tags = soup.find_all('tag')
        for item in tags:
            uprint(item['k'], item['v'])
            
            
def audit(file_name):
    for event, elem in ET.iterparse(file_name, events=('start',)):
        if elem.tag == 'way':
            for tag in elem.iter('tag'):
                if is_street_name(tag):
                    x=1

def count_tags(file_name):
    tags = {}
    for event, elem in ET.iterparse(file_name):
        if elem.tag in tags:
            tags[elem.tag] += 1
        else:
            tags[elem.tag] = 1
    
    print('tag : count')
    for key in tags:
        print(key, ':', tags[key])

    return tags


count_tags(OSM_FILE)

#resize_map()      
#analise(SAMPLE_FILE)
