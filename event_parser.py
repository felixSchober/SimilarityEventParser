from Evtx.Evtx import Evtx
from Evtx.Views import evtx_file_xml_view
from lxml import etree
import re
from tqdm import tqdm
import os

def to_lxml(record_xml):
    record_xml = record_xml.replace('\n', '')
    x = etree.fromstring(f'<?xml version="1.0" standalone="yes" ?>{record_xml}')
    return x

def get_records(filename):
    with Evtx(filename) as evtx:
            for xml, record in evtx_file_xml_view(evtx.get_file_header()):
                try:
                    yield to_lxml(xml), None
                except etree.XMLSyntaxError as e:
                    yield xml, e
                    
def parse_raw_data(xml, write_to):
    xml = xml_escape(xml)

    try:
        data = etree.fromstring(f'<data>{xml}</data>')
    except etree.XMLSyntaxError as e:
        write_to('\nSyntax error parsing this node: ' + xml)
        write_to(e)
        return None
    return data


def xml_escape(xml):
    xml = xml.replace('<=', '&lt;')
    xml = xml.replace('>=', '&gt;')
    xml = xml.replace(' < ', ' &lt; ')
    xml = xml.replace(' > ', ' &gt; ')
    xml = xml.replace('&', '&amp;')
    return xml

def load_data(eventX_dir, event_id, parse_data):
    
    print('Loading data from directory ' + eventX_dir)
    print('This process can a long time. Please be patient')
    filename = ''
    file_progress = tqdm(os.listdir(eventX_dir), desc='Processing ' + filename, unit='file')
    df_content = []

    for filename in file_progress:
        if not filename.endswith(".evtx"): 
            file_progress.write('Skipping ' + filename)
            continue
        
        filepath = os.path.join(eventX_dir, filename)
        df_content = parse_file(filepath, event_id, df_content, parse_data, file_progress)
    return df_content


def parse_file(filepath, event_id, df_content, parse_data, file_progress):
    for node, err in get_records(filepath):
        if err is not None:
            continue
            
        n_eId = node[0][1]
        if (event_id is not None and int(n_eId.text) != event_id):
            continue
                        
        df_row = {
            'EventID': n_eId.text,
            'Level': node[0][2].text,
            'Computer': node[0][8].text,
            'SimilarId': 0,
            'Similarity': 0.0,
            'NumberOfSimilarEntries': 0
        }
        
        if parse_data:
            data = parse_raw_data(node[1][0].text, file_progress.write)
            if data is not None:
                df_row['executionTime'] = data[0].text
                df_row['query'] = data[-1].text.replace('\t', '')
            else:
                df_row['executionTime'] = -1 
                df_row['query'] = node[1][0].text
        else:
            df_row['raw_data'] = node[1][0].text
        
        df_content.append(df_row)
    return df_content