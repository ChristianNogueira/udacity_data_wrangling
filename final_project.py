#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser
import xml.etree.ElementTree as ET  # Use cElementTree or lxml if too slow
from bs4 import BeautifulSoup

project_path = "C:\\Users\\christian\\Documents\\udacity\\data_wrangling"
file_osm = os.path.join(project_path, 'data', 'sao-paulo_moema.osm')
file_osm_small = os.path.join(project_path, 'data', 'sao-paulo_moema_small.json')
file_json = os.path.join(project_path, 'data', 'sao-paulo_moema.json')

config = configparser.ConfigParser()
config.read(os.path.join(project_path,'udacity.ini')

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file) 

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

def custom_osm_reader(file_name):
    #read osm files and return custom data dict
    tree = ET.parse(file_name)
    root = tree.getroot()
    data =[]
    
    for first_level in root:
        item_mask = {}
        item_mask['type'] = first_level.tag
        for attri in first_level.attrib:
            item_mask[attri] = first_level.attrib[attri]
        
        #capture n tags 'tag' attributes inside first tag
        tag_holder = []
        for second_level in first_level:
            item_mask_2 ={}
            for attri_2 in second_level.attrib:
                item_mask_2[attri_2] = second_level.attrib[attri_2]

            tag_holder.append(item_mask_2)
            
        item_mask['tag'] = tag_holder
        data.append(item_mask)
        
    return data
    
def save_to_json(data, file_path):
    #save dict data into a json file
    with open(file_path, 'w') as fp:
        json.dump(data, fp)

def store_to_mongo(file_json, conn)
    pass

data = custom_osm_reader(file_osm)

#save_to_json(data, file_json)
#count_tags(file_osm)
#resize_map()      
#analise(file_osm_small)
