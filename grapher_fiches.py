import json
import pydot # try using networkX instead

def get_label(word, attrs):
    if 'p' in attrs['tags']:
        label = '/' + word # using word as label
    else:
        label = '.' + word

    if attrs['translations'] != []:
        translation = str(attrs['translations'])[1:-1] # attrs['translations'][0]

        if len(translation.split(' ')) > 4:
            label += '\n('
            k = 0
            sections = translation.split(' ')
            section = ""
            while k < len(sections):
                section += sections[k] + ' '
                if k % 3 == 2:
                    if k > 2: # not the first iteration
                        label += '\n'
                    label += section
                    section = ""
                k += 1
            if k % 3 != 0: # car k += 1
                label += '\n' + section
            label = label[:-1] + ')'

        else:
            label += '\n(' + translation + ')'

    i = 0
    desc = attrs['description'].split(' ')
    m = len(desc)
    if len(desc) > 1:
        while i < m:
            if i % 4 == 0:
                label += '\n'
            label += desc[i] + ' '
            i += 1

    return label


def get_graph(data): # data is the json file

    words = []
    classes = {}
    colors = {}
    groups = {} # groups of words to be displayed in a separate table

    for word, attrs in data.items(): # registering base words
        if attrs['type'] == 'class' or attrs['type'] == 'special' or attrs['type'] == 'pronoun' or attrs['type'] == 'state':
            classes[word] = {'label': get_label(word, attrs), 'words': []} # creating empty subdict
        if attrs['type'] == 'color' or attrs['type'] == 'numeral':
            colors[word] = {'label': get_label(word, attrs), 'words': []} # creating empty subdict
        else:
            continue

    for word, attrs in data.items(): # adding nodes

        label = get_label(word, attrs)

        if attrs['type'] == 'simple noun':
            type = 'noun'
        elif attrs['type'] == 'compound':
            type = 'compound'
        else:
            continue
    
        # appending to base classes

        word_instance = {'code': word, 'label': label} # word data to add to the many pages

        if type == 'noun':
            for component in word.split(' '):
                if component in classes.keys():
                    classes[component]['words'].append(word_instance)
                else:
                    if component not in colors.keys(): # default behavior : create a new color class
                        colors[component] = {'label': "", 'words': []} # creating empty dict
                    colors[component]['words'].append(word_instance)

        elif type == 'compound':
            class_word = word.split(' ')[-1]
            
            if class_word not in classes.keys():
                classes[class_word] = {'label': "", 'words': []} # creating empty dict
            classes[class_word]['words'].append(word_instance)

        # adding word group instances

        for tag in attrs['tags']:
            if tag != 'p':
                if tag not in groups.keys():
                    groups[tag] = []
                groups[tag].append(word_instance)
            
        for translation in attrs['translations']:
            if translation not in groups.keys():
                groups[translation] = []
            groups[translation].append(word_instance)

    
    # SORTING DICT
    for dict_, type_name in [(classes, 'class'), (colors, 'color')]:
        for word, attrs in dict_.items():
            x = len(words) # len of words list
            y = len(attrs['words'])
            i = 0
            while i < x and y > len(words[i]['words']):
                i += 1
            words.insert(i, {'code': word, 'type': type_name, 'label': attrs['label'], 'words': attrs['words']})

    del_keys = []
    for key, values in groups.items():
        if len(values) <= 1: # values are lists, removing lists that have only one element
            del_keys.append(key)
    for key in del_keys:
        del groups[key]

    with open('groups.json', 'w') as f:
        json.dump({'entries': words, 'groups': groups}, f, indent=4)


with open('nyo.json', 'r') as f:
    data = json.load(f)
    get_graph(data)


