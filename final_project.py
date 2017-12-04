#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import re
import sys
import json
import unidecode
import configparser
import xml.etree.ElementTree as ET
from pymongo import MongoClient
from bs4 import BeautifulSoup

project_path = "C:\\Users\\christian\\Documents\\udacity\\data_wrangling"
file_osm = os.path.join(project_path, 'data', 'sao-paulo_moema.osm')
file_osm_small = os.path.join(project_path, 'data', 'sao-paulo_moema_small.json')
file_json = os.path.join(project_path, 'data', 'sao-paulo_moema.json')

# MongoDb Atlas connection credentials
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
        # fix udacity function including b at string
        output.write(b'<?xml version="1.0" encoding="UTF-8"?>\n')
        output.write(b'<osm>\n  ')
    
        # Write every kth top level element
        for i, element in enumerate(get_element(OSM_FILE)):
            if i % k == 0:
                output.write(ET.tostring(element, encoding='utf-8'))
    
        output.write(b'</osm>')

def count_tags(file_name):
    """Count all tags of osm from OpenStreetMap file
    Args:
        file_name: absolute path of osm file
    Returns:
        Dictionary with tag as key and number of occurrences as value and print
        the values
    Raises:
    """
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
    """Read OSM from OpenStreetMap
    Args:
        file_name: absolute path of osm file
    Returns:
        List of dictionaries containing data fom the tags
        'node', 'way' and 'relation'. The <tag> tag is stored as a dictionary
        containing the attributes 'k' as key and 'v' as value
    Raises:
    """
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
            tag_holder = {}
            for second_level in first_level:

                if all (key in second_level.attrib for key in ("k", "v")):
                    # inside tag we just desire the k (key) and v (value) attributes
                    tag_holder[second_level.attrib['k']] = second_level.attrib['v']
                
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

def available_minor_tags(data, tag_major):
    """Available key values inside 'tag' dictionary
    Args:
        data: data from the function custom_osm_reader
        tag_major: major tag to be analyzed, possible values are 'node', 'way' and 'relation'
    Returns:
        Dictionary containing distinct values and count of occurences
    Raises:
    """
    tag_minor = {}
    for entry in data:
        if entry['type'] == tag_major:
            for tag in entry['tag']:
                if tag in tag_minor:
                    tag_minor[tag] += 1
                else:
                    tag_minor[tag] = 1
    return tag_minor


def data_view(data, tag_major, tag_minor, regex):
    """List all tags values applying filter to 'tag' dictionary with Regex
    Args:
        data: data from the function custom_osm_reader
        tag_major: major tag to be analyzed, possible values are 'node', 'way' and 'relation'
        tag_minor: key values within 'tag' key dictionary
        regex: regex expression to be applied to 'tag' dictionary value
    Returns:
        Print and returns Distinct values from the 'tag' dictionary inside 'node', 'way' or 'relation' with 
        the desired regex applied, with counted occurrences and sorted by alphabetical.
        '.*' May be assigned as regex to return all possible values
    Raises:
    """
    street_ref_count = {}
    street_regex = re.compile(regex)
    for entry in data:
        # filter only desired tag_major
        if entry['type'] == tag_major:
            # data has no fixed schemma, verify if tag_minor exists first
            if tag_minor in entry['tag']:
                street_ref = street_regex.match(entry['tag'][tag_minor])
                if street_ref:
                    if street_ref.group(0) in street_ref_count:
                        street_ref_count[street_ref.group(0)] += 1
                    else: 
                        street_ref_count[street_ref.group(0)] = 1
    
    # sorted by key, print to identify problems
    for key, value in sorted(street_ref_count.items()):
        print("%s: %s" % (key, value))
    
    return street_ref_count

def statistics_mongo():
    with MongoClient(conn_mongo) as client:
        db = client.final_project
        
        print("Total de registros no database")
        print(db.sao_paulo_moema.find().count())
        
def data_cleaning_names(data, minor_tag):
    """Removes diacritics and get first word
    Args:
        data: data from the function custom_osm_reader
        tag_minor: key values within 'tag' key dictionary
    Returns:
        Data with a included key in the 'tag' dictionary, maintaining the original minor_tag
        and a new named as minor_tag + '_clean'
    Raises:
    """
    new_tag = minor_tag + '_clean'
    regex = '^.+?(\s|$)'
    # pre compile regex for performance improvement
    re_compiled = re.compile(regex)
    
    for i, entry in enumerate(data):
        if 'tag' in entry:
            # data has no fixed schemma, verify if tag_minor exists first
            if minor_tag in entry['tag']:
                # unidecode finds the closest character without diacritics
                find_match = re_compiled.match(unidecode.unidecode(data[i]['tag'][minor_tag]))
                if find_match:
                    data[i]['tag'][new_tag] = find_match.group(0)

    return data

def data_cleaning_website(data):
    """Standardize websites URL, removes http, https, returns only root site up to first /
        and returns domain of site
    Args:
        data: data from the function custom_osm_reader
    Returns:
        Data with new key called "website_clean" and "website_domain"
    Raises:
    """
    regex_clean = r'[a-z0-9\-.]+\.[a-z]{2,3}'
    regex_domain = r'(\.[a-z]{2,3}){1,2}(\.[a-z]{2,3})?$'
    # pre compile regex for performance improvement
    re_clean_compiled = re.compile(regex_clean)
    re_doamin_compiled = re.compile(regex_domain)
    
    for i, entry in enumerate(data):
        if 'tag' in entry:
            if 'website' in entry['tag']:
                # makes all lowercase
                website_clean = data[i]['tag']['website'].lower()
                # removes http:// and https://
                if website_clean[:7] == 'http://':
                    website_clean = website_clean[7:] 
                if website_clean[:8] == 'https://':
                    website_clean = website_clean[8:]
                
                find_match = re_clean_compiled.match(website_clean)
                if find_match:
                    website_clean = find_match.group(0)
                
                # removes www.
                if website_clean[0:4] == 'www.':
                    website_clean = website_clean[4:]
                    
                data[i]['tag']['website_clean'] = website_clean
                
                # gather domain of site
                find_match = re_doamin_compiled.search(website_clean)
                if find_match:
                    data[i]['tag']['website_domain'] = find_match.group(0)
                
    return data
    
# --------------------------------
print(count_tags(file_osm))

data = custom_osm_reader(file_osm)

print('Way tags available')
print(available_minor_tags(data, 'way'))
print('Node tags available')
print(available_minor_tags(data, 'node'))

# Values to be cleaned
data_view(data, 'node', 'website', '.*')
data_view(data, 'way', 'website', '.*')
data_view(data, 'node', 'name', '.*')

# Cleaning process
data_cleaned_website = data_cleaning_website(data)
data_cleaned = data_cleaning_names(data_cleaned_website, 'name')
save_to_json(data_cleaned, file_json)

# Upload and status
store_json_mongo(file_json, conn_mongo)
statistics_mongo()
