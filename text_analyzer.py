from sklearn.feature_extraction.text import CountVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from tqdm import tqdm, trange
import event_parser
import os
import pandas as pd 


TEMP_EXTRACTED_DF_NAME = 'extractedDf.pkl'
TEMP_EXTRACTED_SIM_DF_NAME = 'simDf.pkl'

def __get_cosine_sim(strings): 
    vectors = [t for t in __get_vectors(strings)]
    return cosine_similarity(vectors)
    
def __get_vectors(text):    
    vectorizer = CountVectorizer(text)
    vectorizer.fit(text)
    return vectorizer.transform(text).toarray()

def __get_dataframe(eventX_dir, event_id, parse_data, temp_dir):
    temp_path = os.path.join(temp_dir, TEMP_EXTRACTED_DF_NAME)
    if os.path.exists(temp_path):
        df = pd.read_pickle(temp_path)
        print('DF loaded')
    else:
        df_content = event_parser.load_data(eventX_dir, event_id, parse_data)

        if len(df_content) == 0:
            raise Exception('Could not find any events with event id ' + str(event_id))

        df = pd.DataFrame(df_content)
        print('DF created')

        df.to_pickle(temp_path)
        print(f'DF saved ({temp_path})')
    return df

def __get_similarity_dataframe(df, sim_threshold, temp_dir):
    temp_path = os.path.join(temp_dir, TEMP_EXTRACTED_SIM_DF_NAME)
    if os.path.exists(temp_path):
        sim_df = pd.read_pickle(temp_path)
        print('DF loaded')        
    else:
        sentences = df['query'].tolist()
        print('Creating similarity matrix')
        similarities = __get_cosine_sim(sentences)
        print('Matrix created')

        print('Creating similarity data frame')
        
        df_content = __calculate_similarities(similarities, df, sim_threshold, sentences)

        print('Similarities created')


        sim_df = pd.DataFrame(df_content)
        sim_df.to_pickle(temp_path)
        print(f'DF saved ({temp_path})')
    return sim_df

def __calculate_similarities(similarities, df, sim_threshold, sentences):
    sim_id = 0
    df_content = []
    used_events = []
    progress_bar = trange(df.shape[0], unit='Events')
    for row_i in progress_bar:
        sim_id += 1
        
        if row_i in used_events:
            continue

        entry_text = sentences[row_i]
        current_entry = df.loc[row_i].to_dict()
        current_entry['SimilarId'] = sim_id
        used_events.append(row_i)        
        numberOfSimilarEntries = 0
        for sim_i in trange(df.shape[0], leave=False):
            # prevent comparing to itself
            if row_i == sim_i or sim_i in used_events:
                continue
                
            if similarities[row_i][sim_i] >= sim_threshold:
                used_events.append(sim_i)

                numberOfSimilarEntries += 1

                # match
                current_sim_entry = df.loc[sim_i].to_dict()
                current_sim_entry['SimilarId'] = sim_id
                df_content.append(current_sim_entry)
                
        
        if numberOfSimilarEntries > 0:
            progress_bar.write(f"[{sim_id}] Entry {sim_id} - {entry_text[0:70]}: Similar Entries: {numberOfSimilarEntries}")
        
        current_entry['NumberOfSimilarEntries'] = numberOfSimilarEntries
        df_content.append(current_entry)

    return df_content

def __group_export(df, sim_df, output_filename):
    print('Group DF')
    sim_grouped = sim_df.groupby('SimilarId').sum()
    print('Group finished')
    
    print('Save excel. Output filename: ' + output_filename)
    with pd.ExcelWriter(output_filename) as writer:  
        df.to_excel(writer, sheet_name='All')
        sim_df.to_excel(writer, sheet_name='Similar')
        sim_grouped.to_excel(writer, sheet_name='Similar Grouped')

def analyze(eventX_dir, event_id, parse_data=True, temp_dir='temp', sim_threshold=0.95):
    df = __get_dataframe(eventX_dir, event_id, parse_data, temp_dir)
    sim_df = __get_similarity_dataframe(df, sim_threshold, temp_dir)
    __group_export(df, sim_df, 'output.xlsx')
