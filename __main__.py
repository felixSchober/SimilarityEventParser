from Evtx.Evtx import Evtx
from Evtx.Views import evtx_file_xml_view
from lxml import etree
import pandas as pd 
from sklearn.metrics.pairwise import cosine_similarity
from collections import Counter
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import os
import re
from tqdm import tqdm

def get_cosine_sim(strs): 
    vectors = [t for t in tqdm(get_vectors(strs))]
    return cosine_similarity(vectors)
    
def get_vectors(text):
    #text = [t for t in strs]
    #print(text)

    vectorizer = CountVectorizer(text)
    vectorizer.fit(text)
    return vectorizer.transform(text).toarray()

def get_child(node, tag, ns="{http://schemas.microsoft.com/win/2004/08/events/event}"):
    """
    @type node: etree.Element
    @type tag: str
    @type ns: str
    """
    return node.find("%s%s" % (ns, tag))

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
                    
def parse_raw_data(xml):
    xml = xml.replace('<=', '&lt;')
    xml = xml.replace('>=', '&gt;')
    xml = xml.replace(' < ', ' &lt; ')
    xml = xml.replace(' > ', ' &gt; ')
    xml = xml.replace('&', '&amp;')


    try:
        data = etree.fromstring(f'<data>{xml}</data>')
    except etree.XMLSyntaxError as e:
        print('\nSyntax error parsing this node: ' + xml)
        print(e)
        return None
    return data


event_id = '1309'
df_content = []
parse_data = True
sim_thres = 0.95
evtx_dir = os.path.join(os.getcwd(), 'events')

if os.path.exists(os.path.join(os.getcwd(), 'extractedDf.pkl')):
    df = pd.read_pickle("./extractedDf.pkl")
    print('DF loaded')
else:

    for filename in tqdm(os.listdir(evtx_dir)):
        if not filename.endswith(".evtx"): 
            continue        
        
        filepath = os.path.join(evtx_dir, filename)
        for node, err in get_records(filepath):
            if err is not None:
                continue
                
            n_eId = node[0][1]
            if (event_id is not None and n_eId.text != event_id):
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
                data = parse_raw_data(node[1][0].text)
                if data is not None:
                    df_row['executionTime'] = data[0].text
                    df_row['query'] = data[-1].text.replace('\t', '')
                else:
                    df_row['executionTime'] = -1 #re.sub(pattern, repl, string, max=0)
                    df_row['query'] = node[1][0].text
            else:
                df_row['raw_data'] = node[1][0].text
            
            df_content.append(df_row)

            
    df = pd.DataFrame(df_content) 
    print('DF created')
    df.to_pickle("./extractedDf.pkl")
    print('DF saved')

if os.path.exists(os.path.join(os.getcwd(), 'simDf.pkl')):
    sim_df = pd.read_pickle("./simDf.pkl")
    print('DF loaded')
    
else:

    sentences = df['query'].tolist()
    print('Sentences created')

    print('Creating similarity matrix')
    similarities = get_cosine_sim(sentences)
    print('Matrix created')
    print('Creating similarity data frame')
    sim_id = 0
    df_content = []
    used_events = []
    for row_i in tqdm(range(df.shape[0])):
        #if df.at[row_i, 'SimilarId'] > 0:
        #    current_sim_id = df.at[row_i, 'SimilarId']
        #    print(df.at[row_i, 'SimilarId'])
        #else:
        #    current_sim_id = sim_id
        #    df.at[sim_i, 'SimilarId'] = current_sim_id

        sim_id += 1
        
        if row_i in used_events:
            continue

        entry_text = sentences[row_i]
        current_entry = df.loc[row_i].to_dict()
        current_entry['SimilarId'] = sim_id
        used_events.append(row_i)

        #print('\n[' + str(sim_id) + '] Entry ' + str(row_i) + ' - ' + entry_text[0:70])
        numberOfSimilarEntries = 0
        for sim_i in range(df.shape[0]):
            # prevent comparing to itself
            if row_i == sim_i or sim_i in used_events:
                continue
                
            if similarities[row_i][sim_i] >= sim_thres:
                used_events.append(sim_i)

                numberOfSimilarEntries += 1
                # match
                current_sim_entry = df.loc[sim_i].to_dict()
                current_sim_entry['SimilarId'] = sim_id
                df_content.append(current_sim_entry)
                #df.at[sim_i, 'SimilarId'] = current_sim_id
                #print('\tEntry ' + str(sim_i) + ' is similar: ' + str(similarities[row_i][sim_i]) + ' - ' + sentences[sim_i][0:70])
            #else:
                #df_content.append(df.loc[sim_i].to_dict())
        current_entry['NumberOfSimilarEntries'] = numberOfSimilarEntries
        df_content.append(current_entry)


    print('Similarities created')
    sim_df = pd.DataFrame(df_content)
    sim_df.to_pickle("./simDf.pkl")
    print('DF saved')
print('Group DF')
#grouped_df = pd.DataFrame(sim_df.groupby('SimilarId').size(),columns=['Count'])
sim_grouped = sim_df.groupby('SimilarId').sum()
print('Group finished')
#sim_df.to_pickle("./simDf_Grouped.pkl")
#print('Grouped by DF saved')
print('Save excel')
with pd.ExcelWriter('output.xlsx') as writer:  
    df.to_excel(writer, sheet_name='All')
    sim_df.to_excel(writer, sheet_name='Similar')
    sim_grouped.to_excel(writer, sheet_name='Similar Grouped')
print('Process finished')
        
