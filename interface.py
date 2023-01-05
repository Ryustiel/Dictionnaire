import json
import webbrowser
import os
from grapher import get_graph
from grapher_plot import get_graph as get_graph_plot
from flask import Flask, render_template, request, redirect

def get_unique_id(data: dict) -> str: # dict from json file
    ids = []
    for word, attrs in data.items():
        if word[0] == '/': # is a temporary id
            ids.append(int(word[1:])) # following a /, it's all digits
    if ids == []:
        return '/1'
    else:
        m = max(ids)
        return f"/{str(m+1)}" # returns next id for creating a new temporary id


app = Flask("test", template_folder=os.getcwd())

@app.route('/')
def main():
    with open('nyo.json', 'r') as f:
        data = json.load(f)
        get_graph(data)

    with open('nyo.svg', 'r') as f:
        svg = f.read()

    get_graph_plot(data)

    with open('nyo.svg', 'r') as f:
        svg_plot = f.read()
        return render_template('index.html', graph=svg, graph_plot=svg_plot)


@app.route('/add', methods=['POST'])
def add():
    input_field = request.form['input']
    word_type = request.form['type']
    if 'is-description' in request.form.keys():
        is_description = True
    else:
        is_description = False

    with open('nyo.json', 'r') as f:
        data = json.load(f)

    if is_description:
        # Actually just puts an additional tag
        if input_field in data:
            return redirect('/')
        data[input_field] = {
            'description': '',
            'tags': ['p'],
            'translations': [],
            'type': word_type
        }
    else:
        # Check if the input is a key
        if input_field in data:
            return redirect('/')
        data[input_field] = {
            'description': '',
            'tags': [],
            'translations': [],
            'type': word_type
    }

    with open('nyo.json', 'w') as f:
        json.dump(data, f, indent=4)

    # rechargement du graph

    with open('nyo.json', 'r') as f:
        data = json.load(f)
        node = data[input_field]
        node['id'] = input_field
        get_graph(data)

    with open('nyo.svg', 'r') as f:
        svg = f.read()

    return render_template('modify.html', graph=svg, node=node)


@app.route('/modify', methods=['POST'])
def modify_node():
    node_id = request.form['node-id']
    with open('nyo.json', 'r') as f:
        data = json.load(f)

    with open('nyo.svg', 'r') as f:
        svg = f.read()
        node = data[node_id]
        node['id'] = node_id
        return render_template('modify.html', graph=svg, node=node)


@app.route('/update', methods=['POST'])
def update_node():
    with open('nyo.json', 'r') as f:
        data = json.load(f)

    node_id = request.form['node-id']
    # Retrieve the updated data for the node from the form submission
    word = request.form['word'] if 'word' in request.form.keys() else None
    description = request.form['description'] if 'description' in request.form.keys() else ""
    type = request.form['type']
    tags = request.form['tags'].split(',') if 'tags' in request.form.keys() else []
    translations = request.form['translations'].split(',') if 'translations' in request.form.keys() else []
    
    if tags == [""]:
        tags = []
    if translations == [""]:
        translations = []

    if word is None or word == '':
        data.pop(node_id) # deleting the node (node_id = word (previous value))

    else:
        if not word in data.keys():
            data[word] = {}
        data[word]['description'] = description
        data[word]['type'] = type
        data[word]['tags'] = tags
        data[word]['translations'] = translations

        if node_id != word:
            data.pop(node_id) # node has been renamed

    with open('nyo.json', 'w') as f:
        json.dump(data, f, indent=4)

    return redirect('/')


if __name__ == '__main__':
    webbrowser.open('http://localhost:5000')
    app.run()   
