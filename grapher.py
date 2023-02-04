import json
import pydot # try using networkX instead

def get_graph(data): # data is the json file

    # Create a graph
    graph = pydot.Dot(graph_type='graph', id='svg-graph', layout='dot', nodesep='0.0', sep='1', center='-50', maxiter='10000', overlap='scale', ratio='fill') # graphdir, neato, twopi, circo, fdp, dot

    # Create a dictionary to store the nodes
    nodes = {}

    for word, attrs in data.items(): # adding nodes

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

        if attrs['type'] == 'color' or attrs['type'] == 'numeral':
            linetype = 'dotted'
        elif attrs['type'] == 'class':
            linetype = 'dashed'
        else:
            linetype = 'solid'

        fillcolor = 'white'
        if word[0] == '/' or 'pending' in attrs['tags'] or 'p' in attrs['tags']:
            color = 'orange'
            fillcolor = 'beige'
        elif attrs['type'] == 'special' or attrs['type'] == 'pronoun':
            color = 'gray'
        else:
            color = 'black'

        node = pydot.Node(word, label=label, color=color, fillcolor=fillcolor, style='filled') # creates a node for the current word
        node.set_id(word)
        node.set_style(linetype)
        graph.add_node(node)
        nodes[word] = node

    for label in ['numeral', 'pronoun', 'state', 'special']:
        node = pydot.Node(label, label=label, color='azure3', fillcolor='azure3', style='filled')
        graph.add_node(node)
        nodes[label] = node

    used_up = [] # nodes that have been edged already

    # Iterate through the words in the JSON file for setting edges
    for word, attrs in data.items():

        translations = attrs['translations'] # Get the list of translations for the current word

        for label in ['numeral', 'pronoun', 'state', 'special']:
            if attrs['type'] == label:
                edge = pydot.Edge(nodes[word], nodes[label]) # Create an edge with the numerals node
                edge.set_style('solid')
                edge.set_color('azure2')
                graph.add_edge(edge)

        unique_numeral_link = True
        for other_word, other_attrs in data.items(): # Iterate through the other words in the JSON file
            
            if other_word == word: # Skips self
                continue

            if (attrs['type'] != 'simple noun') and other_attrs['type'] == 'simple noun': 
                
                components = other_word.split() # Split the word into components
                
                if any(c == word for c in components): # Check if any of the components is equal to the current word
                    edge = pydot.Edge(nodes[word], nodes[other_word]) # Create an edge between the two nodes
                    if attrs['type'] == 'color':
                        edge.set_style('dotted')
                    else:
                        edge.set_style('dashed')
                    graph.add_edge(edge)
                    continue

            other_translations = other_attrs['translations'] # Get the list of translations for the other word

            if (not other_word in used_up) and any(t != "" and t in other_translations for t in translations): # Check if the current word and the other word share at least one direct translation
                edge = pydot.Edge(nodes[word], nodes[other_word]) # Create an edge between the two nodes
                edge.set_style('solid')
                graph.add_edge(edge)

            if (not other_word in used_up) and any(t != "" and t != "p" and t in other_attrs['tags'] for t in attrs['tags']): # Check if the current word and the other word share at least one direct translation
                edge = pydot.Edge(nodes[word], nodes[other_word]) # Create an edge between the two nodes
                edge.set_style('solid')
                edge.set_color('gray')
                graph.add_edge(edge)

            """
            if unique_numeral_link and (not other_word in used_up) and attrs['type'] == 'numeral' and other_attrs['type'] == 'numeral': # edge between all numerals
                edge = pydot.Edge(nodes[word], nodes[other_word]) # Create an edge between the two nodes
                edge.set_style('dotted')
                graph.add_edge(edge)
                unique_numeral_link = False

            if unique_numeral_link and (not other_word in used_up) and attrs['type'] == 'pronoun' and other_attrs['type'] == 'pronoun': # edge between all numerals
                edge = pydot.Edge(nodes[word], nodes[other_word]) # Create an edge between the two nodes
                edge.set_style('solid')
                edge.set_color('gray')
                graph.add_edge(edge)
                unique_numeral_link = False
            """

        used_up.append(word) # add it there so it isn't added twice

    graph.write_svg('nyo.svg')