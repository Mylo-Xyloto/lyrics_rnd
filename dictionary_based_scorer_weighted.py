import os
import json
from text_cleaner import clean_text
import pandas as pd
from collections import OrderedDict
from math import log2

classes = ('destressing', 'distracting', 'motivating', 'reappraisal', 'suppressing', 'uplifting')
postfix = '_collection_by_tushar'
postfix = ''
lyrics_dir = '../archive/all_lyrics'
id2title_path = 'ID2TITLE' + postfix + '.json'
out_dir = 'classification_result'
keywords_dir = "keywords"


def build_dictionary(keywords_filename):
    """This function takes the main keywords xlsx file path and returns two JSONs:
        One for the words, one for the weights. """
    word_dictionary = {}
    weight_dictionary = {}

    for c in classes:
        df = pd.read_excel(keywords_filename, c, engine='xlrd').fillna(0)
        words = []
        weights = []
        for row in df.iterrows():
            word, weight = row[1]
            word = word.strip()
            if word:
                if word not in words:
                    words.append(word)
                    weights.append(weight)

        word_dictionary[c] = words
        weight_dictionary[c] = {word: weight for word, weight in zip(words, weights)}

    with open('dictionary' + postfix + '.json', 'w') as fout:
        fout.write(json.dumps(word_dictionary, ensure_ascii=False))
    with open('weights' + postfix + '.json', 'w') as fout:
        fout.write(json.dumps(weight_dictionary, ensure_ascii=False))

    return word_dictionary, weight_dictionary


def prepare_csv_data(dictionary):
    """This function takes the word list JSON and returns the main csv for scoring"""
    with open(id2title_path) as fin:
        i2t = json.load(fin)
    all_words_in_dictionary = list(set([word for wordlist in dictionary.values() for word in wordlist]))
    all_words_in_dictionary.sort()

    data_dict = OrderedDict({'id': [], 'title': []})
    data_dict.update(OrderedDict({w: [] for w in all_words_in_dictionary}))
    for lf in os.listdir(lyrics_dir + postfix):
        ID = lf.split('.')[0]
        with open(lyrics_dir + postfix + '/' + lf) as fin:
            lyrics = clean_text(fin.read())

        data_dict['id'].append(ID)
        data_dict['title'].append(i2t[ID])
        for word in all_words_in_dictionary:
            data_dict[word].append(log2(1 + lyrics.count(word)))  # 2-based log smoothing is applied

    data_df = pd.DataFrame(data_dict)
    data_df.to_csv('data' + postfix + '.csv', index=False)
    return data_df


def generate_classification_result(dictionary, weights, data_df):
    """This function takes the word JSON, weight JSON and main csv dataframe as input and
       and returns the path of an xlsx which contains the result of scoring"""

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    result_df = pd.DataFrame()
    result_df['title'] = data_df['title']
    result_df['url'] = 'https://www.youtube.com/watch?v=' + data_df['id']
    result_for_each_class = {}
    for c in classes:
        score_column = c + '_score'
        scores = []
        for i in range(data_df.shape[0]):
            words_count_series = data_df.iloc[i][dictionary[c]]
            weights_series = pd.Series([weights[c][w] for w in dictionary[c]], index=dictionary[c])/100
            score = (words_count_series*weights_series).sum()
            scores.append(score)
        result_df[score_column] = scores

        top_words_total = 10
        top_words = {i: [] for i in range(top_words_total)}
        for i in range(result_df.shape[0]):
            word_counts = data_df[dictionary[c]].iloc[i].to_dict()
            top_words_and_counts = sorted(word_counts.items(), reverse=True, key=lambda x: x[1])[:top_words_total]
            for j in range(top_words_total):
                if top_words_and_counts[j][1]:
                    cell_value = top_words_and_counts[j][0] + ", " + str(top_words_and_counts[j][1])
                else:
                    cell_value = ""
                top_words[j].append(cell_value)

        for i in range(top_words_total):
            result_df['top_word_' + str(i+1)] = top_words[i]

        result_df_sorted = result_df.sort_values(score_column, ignore_index=False)[::-1]
        result_for_each_class[c] = result_df_sorted
        result_df = result_df.drop(score_column, axis=1)
    out_path = os.path.join(out_dir, 'result.xlsx')
    merge_csv_files_into_xlsx(out_path, result_for_each_class)
    return out_path


def merge_csv_files_into_xlsx(xlsx_path, sheetname_to_dataframe):
    writer = pd.ExcelWriter(xlsx_path, engine='xlsxwriter')
    for sheetname, df in sheetname_to_dataframe.items():
        df.to_excel(writer, sheet_name=sheetname)
    writer.save()


def score_songs(keywords_filename):
    keywords_path = os.path.join(keywords_dir, keywords_filename)
    word_json, weight_json = build_dictionary(keywords_path)
    data_df = prepare_csv_data(word_json)
    result_path = generate_classification_result(word_json, weight_json, data_df)
    return  result_path


if __name__ == "__main__":
    print(score_songs('keywords.xlsx'))
