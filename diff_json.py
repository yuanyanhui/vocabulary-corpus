import json


json_file_1 = "bad_words_questions.json"
json_file_2 = "bad_words_questions_revised.json"

def read_json(json_file_path):
    with open(json_file_path, 'r', encoding='utf-8') as json_file:
        data = json.load(json_file)
    return data

d_o = read_json(json_file_1)
d_r = read_json(json_file_2)

d_diff = []
d_same = []

for do in d_o:
    for dr in d_r:
        if do['id'] == dr['id']: 
            if do['sentence'] != dr['sentence'] or do['distractors'] != dr['distractors']:
                d_diff.append(dr)
            else:
                d_same.append(dr)

print(f"Total questions {len(d_o)}")
print(f"Total revised questions {len(d_diff)}")

with open('bad_words_questions_revised_only.json', 'w', encoding='utf-8') as f:
    json.dump(d_diff, f, indent=4)

with open('bad_words_questions_unrevised.json', 'w', encoding='utf-8') as f:
    json.dump(d_same, f, indent=4)