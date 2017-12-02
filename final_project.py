#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import json
import configparser
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from bs4 import BeautifulSoup

project_path = "C:\\Users\\christian\\Documents\\udacity\\data_wrangling"
file_osm = os.path.join(project_path, 'data', 'sao-paulo_moema.osm')
file_osm_small = os.path.join(project_path, 'data', 'sao-paulo_moema_small.json')
file_json = os.path.join(project_path, 'data', 'sao-paulo_moema.json')

# MongoDb Atlas connection
config = configparser.ConfigParser()
config.read(os.path.join(project_path,'udacity.ini'))
conn_mongo = config['default']['mongo']

def uprint(*objects, sep=' ', end='\n', file=sys.stdout):
    # use when getting error with print caused by encoding
    enc = file.encoding
    if enc == 'UTF-8':
        print(*objects, sep=sep, end=end, file=file)
    else:
        f = lambda obj: str(obj).encode(enc, errors='backslashreplace').decode(enc)
        print(*map(f, objects), sep=sep, end=end, file=file) 

def get_element(osm_file, tags=('node', 'way', 'relation')):
    # resize function provided by udacity
    context = iter(ET.iterparse(osm_file, events=('start', 'end')))
    _, root = next(context)
    for event, elem in context:
        if event == 'end' and elem.tag in tags:
            yield elem
            root.clear()

def resize_map():
    # resize function provided by udacity
    k = 20 # Parameter: take every k-th top level element
    with open(SAMPLE_FILE, 'wb') as output:
        output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write(b'<osm>\n  ')
    
        # Write every kth top level element
        for i, element in enumerate(get_element(OSM_FILE)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))
    
        output.write(b'</osm>')

def count_tags(file_name):
    # count total number of tags in osm file
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
    # read osm files and return custom data dict containing tags e attrigutes
    # filter just 'node', 'way' and 'relation' tags
    tree = ET.parse(file_name)
    root = tree.getroot()
    data =[]
    
    for first_level in root:
        if first_level.tag in ['node', 'way', 'relation']:
            item_mask = {}
            item_mask['type'] = first_level.tag
            for attri in first_level.attrib:
                item_mask[attri] = first_level.attrib[attri]
            
            # capture n tags 'tag' attributes inside first tag
            tag_holder = []
            for second_level in first_level:
                item_mask_2 ={}
                
                if all (key in second_level.attrib for key in ("k", "v")):
                    item_mask_2[second_level.attrib['k']] = second_level.attrib['v']
                    tag_holder.append(item_mask_2)
                
            item_mask['tag'] = tag_holder
            data.append(item_mask)
        
    return data
    
def save_to_json(data, file_path):
    # save dict data into a json file
    with open(file_path, 'w') as fp:
        json.dump(data, fp)

def store_json_mongo(file_json, conn):
    # storing using insert, but uploading json with mongoimport is faster
    with MongoClient(conn) as client:
        db = client.final_project
        # if interrupted can resume at same point
        response = db.moema.find().count()
        with open(file_json) as f:
            data = json.loads(f.read())
            # i is 0 index, so if you have 30 items you resume at i = 30 (31th item)
            for i, obs in enumerate(data):
                if i >= response:
                    db.moema.insert(obs)

def data_cleaning(data):
    pass
    return data

def statistics_mongo():
    with MongoClient(conn_mongo) as client:
        db = client.final_project
        
        print("Total de registros no database")
        print(db.sao_paulo_moema.find().count())
        
# --------------------------------
# resize_map()
# count_tags(file_osm)
# data = custom_osm_reader(file_osm)
# data_cleaned = data_cleaning(data)
# save_to_json(data, file_json)
# store_json_mongo(file_json, conn_mongo)
# statistics_mongo()
