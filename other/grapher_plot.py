import json
import networkx as nx
import matplotlib.pyplot as plt

def get_graph(data): # data is the json file

    # Create a graph # id = svg-graph
    graph = nx.Graph()

    for word, attrs in data.items(): # adding nodes
        if word[0] == '/':
            if attrs['translations'] == []: # no word, no translation
                label = attrs['description']
            else: # no word, available translations
                label = ''
                for translation in attrs['translations']:
                    label += translation + ', '
                if label != '':
                    label = label[:-2]
        else:
            label = word # using word as label
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


        if word[0] == '/' or 'pending' in attrs['tags'] or 'p' in attrs['tags']:
            color = (0.2, 0.2, 0.2, 0.05)
    
        elif attrs['type'] == 'special' or attrs['type'] == 'pronoun':
            color = (0.5, 0.5, 0.5, 0.3)

        elif attrs['type'] == 'color' or attrs['type'] == 'numeral':
            color = (0.8, 0.0, 0.8, 0.3)
        
        elif attrs['type'] == 'class':
            color = (1.0, 0.5, 0.0, 0.3)
        
        else:
            color = (0.5, 0.5, 0.5, 0.3)

        graph.add_node(word, label=label, color=color) # creates a node for the current word

    for label in ['numeral', 'pronoun', 'state', 'special']:
        graph.add_node(label, label=label, color=(0.2, 0.2, 0.2, 0.5))

    used_up = [] # nodes that have been edged already

    # Iterate through the words in the JSON file for setting edges
    for word, attrs in data.items():

        translations = attrs['translations'] # Get the list of translations for the current word

        for label in ['numeral', 'pronoun', 'state', 'special']:
            if attrs['type'] == label:
                graph.add_edge(word, label, weight=1, color=(0.5, 0.5, 0.5, 1.0)) # Create an edge with the numerals node

        unique_numeral_link = True
        for other_word, other_attrs in data.items(): # Iterate through the other words in the JSON file
            
            if other_word == word: # Skips self
                continue

            if (attrs['type'] != 'simple noun') and other_attrs['type'] == 'simple noun': 
                
                components = other_word.split() # Split the word into components
                
                if any(c == word for c in components): # Check if any of the components is equal to the current word
                    if attrs['type'] == 'color':
                        weight = 1
                        color = (0.5, 0.0, 0.5, 0.3)
                    else:
                        weight = 2
                        color = (1.0, 0.5, 0.0, 0.3)
                    graph.add_edge(word, other_word, weight=weight, color=color) # Create an edge between the two nodes
                    continue

                    # WEIGHT ATTRIBUTE : NODE SIZE

            other_translations = other_attrs['translations'] # Get the list of translations for the other word

            if (not other_word in used_up) and any(t != "" and t in other_translations for t in translations): # Check if the current word and the other word share at least one direct translation
                graph.add_edge(word, other_word, weight=4, color=(0.5, 0.5, 0.5, 0.3)) # Create an edge between the two nodes

            if (not other_word in used_up) and any(t != "" and t != "p" and t in other_attrs['tags'] for t in attrs['tags']): # Sharing tags
                graph.add_edge(word, other_word, weight=2, color=(0.5, 0.5, 0.5, 0.1)) # Create an edge between the two nodes

        used_up.append(word) # add it there so it isn't added twice

    # fetching graph attributes

    degrees = dict(graph.degree)
    node_size = [600 + d * 800 for d in degrees.values()]

    edge_colors = nx.get_edge_attributes(graph, 'color').values()
    node_colors = nx.get_node_attributes(graph, 'color').values()

    weights = nx.get_edge_attributes(graph, 'weight').values()
    labels = nx.get_node_attributes(graph, 'label')

    edge_colors, node_colors, weights, node_size = list(edge_colors), list(node_colors), list(weights), list(node_size)

    # drawing the graph

    plt.figure(1, figsize=(80, 40))

    pos = nx.spring_layout(graph, k=0.2)

    nx.draw(graph, pos, labels=labels, node_color=node_colors, node_size=node_size, edge_color=edge_colors, width=weights)
    
    plt.savefig('nyo.svg')
    plt.close()



with open("nyo.json", "r") as f:
    data = json.load(f)

    get_graph(data)
    # plt.show()