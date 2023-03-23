data = {
    "fruit": [
            {"label": "apple", "words": [{"code":"123", "label":"pie"}, {"code":"456", "label":"food"}]},
            {"label": "strawberry", "words": [{"code":"225", "label":"cake"}, {"code":"865", "label":"sugar"}]}
        ]
    }

import json
with open("groups.json", "r") as f:
    data = json.load(f)

# write a script that generates a html file with square boxes for each class
# the associated label should be displayed over each box
# and each word should be listed inside the box as an empty link
# align the boxes in a grid so they take the width of the screen (height is unlimited, scrolling is enabled)

with open('output.html', 'w') as f:
    f.write('<html>\n')

    f.write('<head>\n')
    f.write('<style>\n')
    f.write('h2 { text-align: center; font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }\n')
    f.write('body { font-family: "Helvetica Neue", Helvetica, Arial, sans-serif; }\n')
    f.write('.outline { border: 1px solid black; padding: 0.5em; text-align: center; }\n')
    f.write('.outline-orange { background-color: orange; }\n')
    f.write('.outline-purple { background-color: #e6e6fa; }\n')
    f.write('.container { width: 18%; float: left; margin: 0.5%; }\n')
    f.write('p { margin: 0.5em; font-size: 1.5em; }\n')
    f.write('a { text-decoration: none; }\n')
    f.write('a:hover { text-decoration: none; position: relative; }\n')
    f.write('a:hover .box { display: block; position: absolute; left: 0; top: 0; width: 100%; height: 100%; background-color: #e6e6fa; }\n')
    f.write('.box { display: none; }\n')
    f.write('</style>\n')
    f.write('</head>\n')

    f.write('<body>\n')

    for entry in data['entries']:
        f.write('<a href="">\n')
        f.write('<div class="container">\n')

        if entry['type'] == 'class':
            f.write('<h2 style="font-color:orange"')
        else:
            f.write('<h2 style="color:purple"')

        f.write('>{}</h2>\n'.format(entry['code']))

        if entry['type'] == 'class':
            f.write('<div class="outline-orange">\n')
        else:
            f.write('<div class="outline-purple">\n')
        
        for word in entry["words"]:
            f.write('<a href=""><p>{}</p></a><br>\n'.format(word["code"])) # display for label... FEATURE
        f.write('</div>\n')

        f.write('<div class="box">\n')
        f.write('<p>test</p>\n')
        f.write('</div>\n')


        f.write('</div>\n')
        f.write('</a>\n')

    f.write('</body>\n')

    f.write('</html>\n')
