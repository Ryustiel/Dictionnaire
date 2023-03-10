__all__ = ['SVGRenderer', 'hierarchy_layout']
from svgwrite.path import Path
from svgwrite.shapes import Rect, Line, Polygon, Circle
from svgwrite.text import Text, TextPath, TSpan
from svgwrite.container import Marker, Group
from svgwrite import Drawing
import math

_passthrough_ = [
    'font_size',
    'position',
    'rx',
    'ry',
    'fill',
    'stroke',
    'stroke_width',
    'stroke_linecap',
    'stroke_dasharray',
    'marker_fill',
    'marker_stroke_width',
    'marker_units',
    'marker_size',
    'marker_start',
    'marker_mid',
    'marker_end',
]
def DefaultNodeFormatter(node, data):
    props = dict([(key, data[key]) for key in _passthrough_ if key in data])
    label = data.get('label', str(node))
    return str(label), props
def DefaultEdgeFormatter(u, v, data):
    props = dict([(key, data[key]) for key in _passthrough_ if key in data])
    label = data.get('label', '')
    return str(label), props
def midpoint(p1, p2):
    return (p1[0] + p2[0]) * 0.5, (p1[1] + p2[1]) * 0.5

def RichText(s, dy, **kwargs):
    """ parse and create a center aligned multiline Text object:
          dy linespacing.

        coordinates are in viewbox

        vertical baseline is the baseline of the last line

        \\n starts a new line
        \\a makes the line bold
    """
    lines = s.split('\n')
    x, y = kwargs.pop('insert', (0, 0))
    y = y - dy * (len(lines) - 1)
    txt = Text('', insert=(x, y), **kwargs)
    for i, line in enumerate(lines):
        if len(line) > 0:
            if line[0] == '\a':
                line = line[1:]
                font_weight='bold'
            else:
                font_weight='normal'
        else:
            font_weight='normal'
            line = " "
        ts = TSpan(line, x=[x], y=[y + dy * i], 
                font_weight=font_weight, 
                **kwargs)
        txt.add(ts)

    return txt

def hierarchy_layout(g, thresh=6):
    """ layout graph g with a hierarchy. 
        clusters of nodes are at nearby locations.
    """

    import networkx as nx
    pos = {}
    if len(g) < thresh:
        return nx.shell_layout(g)

    g2 = g.subgraph(g.nodes())
    if nx.is_weakly_connected(g2):
        cutset = nx.minimum_edge_cut(g2)
        g2.remove_edges_from(cutset)

    subgraphs = list(nx.weakly_connected_component_subgraphs(g2))
    regions = len(subgraphs)

    if regions == 1:
        return nx.shell_layout(g)
 
    centerg = nx.complete_graph(regions)
    k = (1.0 * regions) ** -0.5
    centerpos = nx.spring_layout(centerg, iterations=20)

    for sgi, sg in enumerate(subgraphs):
        mypos = hierarchy_layout(sg, thresh=thresh)
        for node in mypos:
            pos[node] = [
                    centerpos[sgi][i] + 0.5 * (mypos[node][i] - 0.5) * k for i in range(2)]
    
    return pos

class SVGRenderer(object):
    def __init__(self, 
            GlobalScale=1000., 
            Margin = 100., 
            LineWidth = '1px', 
            FontSize = 20.,
            NodePadding = 0.25,
            EdgeSpacing = 2.,
            LineSpacing = 1.5):
        """ creates a SVGRender with these configurations:

            GlobalScale: units of the image
            Margin: no nodes are placed beyond margin
            LineWidth: width of a line
            FontSize: size of the font for labels

            NodePadding: padding within a node from text to the rect, in FontSize
            LineSpacing: spacing between lines with in a label, in FontSize
            EdgeSpacing: spacing between parallel edges, in FontSize
        """


        self.GlobalScale = GlobalScale
        self.Margin = Margin
        self.LineWidth = LineWidth
        self.FontSize = FontSize
        self.NodePadding = NodePadding
        self.EdgeSpacing = EdgeSpacing
        self.LineSpacing = LineSpacing

    def get_size(self, labeltxt, font_size):
        """ return size of label text in unitary cooridnate """
        lines = labeltxt.split('\n')
        tw = max([len(line) for line in lines]) + self.NodePadding * 2
        th = len(lines) + self.NodePadding * 2
        fac = font_size / self.GlobalScale
        width = tw * fac
        height = th * fac * self.LineSpacing
        return width, height

    def get_anchor(self, pos, otherpos):
        """ returns the anchor point of the edge
            in size of the node box
        """
        anchors = [
                (1.0, 0.5),
                (0.5, 0.0),
                (0., 0.5),
                (0.5, 1.0)]
        diff = (otherpos[0] - pos[0], otherpos[1] - pos[1])
        # the svg coordinate has wrong handness
        ang = math.atan2(-diff[1], diff[0])
        ang = int(ang / math.pi * 180)
        ang += 45
        if ang < 0:
            ang += 360
        if ang >= 360:
            ang -= 360
        phase = ang // 90
        #print pos, otherpos, ang, phase, anchors[phase]
        return anchors[phase]
    def get_anchor2(self, i):
        """ returns the anchor point of the edge
            in size of the node box
        """
        anchors = [
                (1.0, 0.5),
                (0.5, 0.0),
                (0., 0.5),
                (0.5, 1.0)]
        return anchors[i % 4]

    def scale(self, v):
        """ scale from unitary coordinate to SVG viewbox """
        return v[0] * self.GlobalScale, v[1] * self.GlobalScale
    def clip(self, v, s, asp):
        """ clip the position of a node box in unitary coordinate """
        p = self.Margin / self.GlobalScale
        def f(a, b, c):
            if a + b > c - p:
                return c - p- b
            if a < p:
                return p
            return a
        return tuple([f(a, b, c) for a, b, c in zip(v, s, [asp, 1.0])])
    def makemarker(self, symbol, size, stroke, stroke_width, fill, type, units):
        if type == 'marker_start':
            refX, refY = 0.0, 0.5
        if type == 'marker_mid':
            refX, refY = 0.5, 0.5
        if type == 'marker_end':
            refX, refY = 1.0, 0.5
        if symbol[0] in 't.':
            stroke_width = 0
        size1 = size + stroke_width * 2
        sw = stroke_width
        marker = Marker(orient='auto', markerUnits=units, size=(size1, size1), 
                refX=refX * size1, refY=refY * size1)
        if symbol[0] == 't':
            marker.add(Polygon(points=[(sw, sw+0.2 * size), (sw + size, sw + 0.5 * size), (sw, sw + 0.8 * size)], 
                fill=stroke, 
                stroke='none'))
        elif symbol[0] == '.':
            marker.add(Circle(center=(sw + 0.5 * size, sw + 0.5 * size), 
                r=0.5 * size, fill=stroke, stroke='none'))
        elif symbol[0].upper() == 'A':
            marker.add(Polygon(points=[(sw, sw+0.2 * size), (sw + size, sw + 0.5 * size), (sw, sw + 0.8 * size)], 
                fill=fill, stroke=stroke, 
                stroke_width=stroke_width, stroke_linecap='round'))
        elif symbol[0].upper() == 'O':
            marker.add(Circle(center=(sw + 0.5 * size, sw + 0.5 * size), 
                r=0.5 * size, stroke=stroke, fill=fill, stroke_width=stroke_width))
        else:
            raise ValueError("Marker type `%s` unknown" % type)
        return marker

    def draw(self, g, pos=None,
            size=('600px', '400px'), 
            nodeformatter=DefaultNodeFormatter, 
            edgeformatter=DefaultEdgeFormatter):
        """ 

        Draw graph g to a svg file, return the content as a string.

        g: the graph

        pos: position of the nodes given by, for example, networkx.spring_layout

        size: size of the figure in pixels; we will change the view box to GlobalScale,
              thus it is not very relavant.

        nodeformatter returns a string and a dict of rect attributes
            supported rect attributs are:
                stroke, stroke_width, fill, rx, ry

        edgeformatter returns a string and a dict of edge attributes
            supported edge attributs are:
                stroke, stroke_width, fill

                marker_start, marker_end, marker_mid: 
                            'A': triangle shape
                            'o': circle shape
                            't': inside of a triangle
                            '.': inside of a circle
                            'none': no marker
                    marker_mid defaults to 't' for directed graphs

                marker_units: 
                        'strokeWidth': marker_size and marker_stroke_width relative to stroke width
                        'userSpaceOnUse': (default) relative to the userspace unit (GlobalScale)
                                    
                marker_size: size of marker in marker_units
                marker_stroke_width: stroke width of the marker, in marker_units
                marker_stroke: stroke color of a shape marker or the color of 'inside' symbols
                marker_fill: fill color of a shape marker
        """
        dwg = Drawing(size=size) #, profile='basic', version=1.2)
        aspect = 1.0 * int(size[0].replace('px', '')) / int(size[1].replace('px', ''))
        dwg.viewbox(minx=-self.Margin * aspect, miny=-self.Margin, width=aspect * self.GlobalScale + 2 * self.Margin * aspect, height=self.GlobalScale + 2 * self.Margin)
        dwg.fit()
        label_layer = Group()
        node_layer = Group()
        edge_layer = Group()

        dwg.add(node_layer)
        dwg.add(edge_layer)
        dwg.add(label_layer)

        if pos is None:
            pos = hierarchy_layout(g)

        pos = pos.copy()
        x = []
        y = []
        size = {}

        for node, data in g.nodes_iter(data=True):
            label, prop = nodeformatter(node, data)
            font_size = prop.pop('font_size', self.FontSize)
            size[node] = self.get_size(label, font_size)
            if 'position' in prop:
                pos[node] = prop['position']
            p = pos[node]
            x.append(p[0])
            y.append(p[1])

        xmin = min(x)
        xmax = max(x)
        ymin = min(y)
        ymax = max(y)
        # normalize input pos to 0 ~ 1
        for node in g.nodes_iter():
            p = pos[node]
            p = (aspect * (p[0] - xmin) / (xmax - xmin),
                 1.0 * (p[1] - ymin) / (ymax - ymin) )

            wh = size[node]
            p = tuple([p[i] - wh[i] * 0.5 for i in range(2)])
            p = self.clip(p, wh, aspect)
            # shift so that center is correct
            pos[node] = p


        # draw the edges
        drawn = {}

        for u, v, data in g.edges_iter(data=True):
            label, prop = edgeformatter(u, v, data)
            prop.pop('position', 0)

            # parallel edges
            nedges = g.number_of_edges(u, v)
            if g.is_directed():
                nedges += g.number_of_edges(v, u)
            if u <= v:
                key = (u, v)
            else:
                key = (v, u)
            i = drawn.pop((u, v), 0)

            drawn[(u, v)] = i + 1
            i =  2 * i - (nedges - 1)

            p1 = pos[u]
            p2 = pos[v]
            if p1 != p2:
                oldp1 = p1
                oldp2 = p2
                a = self.get_anchor(p1, p2)
                p1 = p1[0] + size[u][0] * a[0], p1[1] + size[u][1] * a[1]
                a = self.get_anchor(p2, p1)
                p2 = p2[0] + size[v][0] * a[0], p2[1] + size[v][1] * a[1]
                p1 = self.scale(p1)
                p2 = self.scale(p2)

                ang = math.atan2((p2[1] - p1[1]), p2[0] - p1[0]) 

                l = ((p2[1] - p1[1]) ** 2 + (p2[0] - p1[0]) ** 2) ** 0.5
                dx = -(p2[1] - p1[1]) / l 
                dy = (p2[0] - p1[0]) / l 

                fac = 1.0
            else:
                a = self.get_anchor2(i)
                p1 = p1[0] + size[u][0] * a[0], p1[1] + size[u][1] * a[1]
                a = self.get_anchor2(i - 1)
                p2 = p2[0] + size[v][0] * a[0], p2[1] + size[v][1] * a[1]
                p1 = self.scale(p1)
                p2 = self.scale(p2)
                ang = math.atan2((p2[1] - p1[1]), p2[0] - p1[0]) 

                l = ((p2[1] - p1[1]) ** 2 + (p2[0] - p1[0]) ** 2) ** 0.5
                dx = -(p2[1] - p1[1]) / l 
                dy = (p2[0] - p1[0]) / l 
                fac = 2.0
            
            # middle of the edge
            txtp = (p1[0] + p2[0]) * 0.5 + fac * self.EdgeSpacing * self.FontSize * i * dx, \
                    (p1[1] + p2[1]) * 0.5 + fac * self.EdgeSpacing * self.FontSize * i * dy 
            # control point
            controlp = tuple([
                    (txtp[i] - (p1[i] + p2[i]) * 0.25) * 2
                    for i in range(2)])
                
            grp = Group()
            stroke_width = prop.pop('stroke_width', self.LineWidth)
            marker_stroke_width = prop.pop('marker_stroke_width', stroke_width)
            fill = prop.pop('fill', 'none')
            marker_fill = prop.pop('marker_fill', 'none')
            stroke = prop.pop('stroke', 'black')
            stroke_linecap = prop.pop('stroke_linecap', 'butt')

            markerUnits = prop.pop('marker_units', 'userSpaceOnUse')
            markerSize = prop.pop('marker_size', self.FontSize)
            font_size = prop.pop('font_size', self.FontSize)
            for type in ['marker_mid', 'marker_start', 'marker_end']:
                symbol = prop.pop(type, 'none')
                if g.is_directed() and type == 'marker_mid' and symbol == 'none':
                    symbol = 't'
                if symbol == 'none': continue
                marker = self.makemarker(symbol=symbol, size=markerSize, 
                        units=markerUnits, stroke_width=marker_stroke_width, 
                        stroke=stroke, fill=marker_fill, type=type)
                dwg.defs.add(marker)
                prop[type] = marker.get_funciri()

            edge = Path(d=[
                    ('M', p1[0], p1[1]), 
                    ('Q', midpoint(p1, controlp), txtp),
                    ('Q', midpoint(controlp, p2), p2),
                    ],
                    stroke_width=stroke_width,
                    fill=fill,
                    stroke=stroke,
                    stroke_linecap=stroke_linecap,
                    **prop)

            edge_layer.add(edge)

            txt = RichText(label, 
                    dy=self.LineSpacing * font_size,
                    font_size=font_size, 
                    font_family='monospace', 
                    text_anchor="middle",
                    insert=txtp, 
                    )
            # I am confused by there is no negtive sign before y diff
            txt.rotate( 180. / math.pi * ang + 180,
                    center=txtp)
            # raise away from the edge by half a line
            txt.translate(tx=0, ty=-font_size * 0.5)
            label_layer.add(txt)

        # draw the nodes
        for node, data in g.nodes_iter(data=True):
            label, prop = nodeformatter(node, data)
            prop.pop('position', 0)
            p = pos[node]
            wh = size[node]
            wh, p = self.scale(wh), self.scale(p)
            grp = Group()
            stroke = prop.pop('stroke', 'black')
            fill = prop.pop('fill', 'none')
            stroke_width = prop.pop('stroke_width', self.LineWidth)
            rx = prop.pop('rx', self.FontSize)
            ry = prop.pop('ry', self.FontSize)
            font_size = prop.pop('font_size', self.FontSize)
            ele = Rect(insert=p, size=wh, 
                    stroke_width=stroke_width,
                    stroke=stroke,
                    fill=fill,
                    rx=rx,
                    ry=ry,
                    **prop
                    )
            node_layer.add(ele)

            txtp =( p[0] + wh[0] * 0.5, 
                    p[1] + wh[1] - self.NodePadding * self.FontSize)

            txt = RichText(label, 
                    dy=self.LineSpacing * font_size,
                    insert=txtp, 
                    font_family='monospace', 
                    font_size=font_size, 
                    text_anchor="middle")

            # raise away from the edge by half a line
            txt.translate(tx=0, ty=-font_size * 0.5)
            label_layer.add(txt)
        return dwg.tostring()

def maketestg():
    import networkx as nx
    import random
    random.seed(9999)
    g = nx.MultiDiGraph()

    g.add_node(range(4))
    g.add_node(range(4))
    g.add_cycle(range(4))
    g.add_edge(5, 5)
    g.add_edge(5, 5)
    
    for node, data in g.nodes_iter(data=True):
        data['value'] = node

    for u, v, data in g.edges_iter(data=True):
        data['value'] = u + v + int(random.random() * 3)
    pos = nx.shell_layout(g)
    return g, pos

def TestNodeFormatter(node, data):
    prop = {}
    prop['stroke_width'] = '%dpx' % (data['value'] + 1)
    colors = ['red', 'green', 'yellow', 'white', 'blue', 'gray']
    prop['fill'] = colors[node]
    prop['stroke'] = colors[(node + 1) % len(colors)]
    return '\aNode[%d]' % node, prop

def TestEdgeFormatter(u, v, data):
    colors = ['red', 'green', 'yellow', 'blue', 'gray']
    prop = {}
    prop['stroke_width'] = '%dpx' % (data['value'] + 1)
    prop['stroke'] = colors[data['value'] % len(colors)]
    markers = 'o.tA'
    prop['marker_size'] = 10.0 # (data['value'] % 3.0  * 2.0 + 4.0) * 5
#    prop['marker_units'] = 'userSpaceOnUse'
    prop['marker_units'] = 'strokeWidth'
    prop['marker_stroke_width'] = 1.0
    prop['marker_fill'] = 'white'
    prop['marker_start'] = markers[(data['value']) % len(markers)]
    prop['marker_mid'] = markers[(data['value'] + 1) % len(markers)]
    prop['marker_end'] = markers[( data['value'] + 2) % len(markers)]
    return '\aEdge\n[%d, %d]' % (u, v), prop

def test():
    import networkx as nx
    #pos = nx.spring_layout(g)
    from sys import stdout
    g, pos = maketestg()
    red = SVGRenderer(EdgeSpacing=4.0) 
    stdout.write(red.draw(g, pos, nodeformatter=TestNodeFormatter, edgeformatter=TestEdgeFormatter))

def testmpl():
    from sys import stdout
    import networkx as nx
    from matplotlib.figure import Figure
    from matplotlib.backends.backend_agg import FigureCanvasAgg
    fig = Figure(figsize=(9, 9))
    fig.set_facecolor('white')
    canvas = FigureCanvasAgg(fig)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axison = False
    ax.invert_yaxis()
    g, pos = maketestg()
    labels = {}
    for node, data in g.nodes_iter(data=True):
        labels[node] = DefaultNodeFormatter(node, data)
    edge_labels = {}
    for u, v, data in g.edges_iter(data=True):
        edge_labels[u, v] = DefaultEdgeFormatter(u, v, data)

    #nx.draw_networkx_nodes(g, pos, ax=ax)
    nx.draw_networkx_labels(g, pos, labels, ax=ax, bbox=dict(pad=10, edgecolor='k'))
    nx.draw_networkx_edges(g, pos, ax=ax)
    nx.draw_networkx_edge_labels(g, pos, edge_labels, ax=ax)
    canvas.print_svg(stdout, dpi=100)

def install_repr_svg():
    import networkx as nx
    def getsvg(graph):
        try:
            pos = nx.graphviz_layout(graph)
            raise Exception()
        except Exception as e:
            pos = hierarchy_layout(graph)
        GlobalScale=len(graph) ** 0.6 * 300.
        rend = SVGRenderer(
            GlobalScale=GlobalScale,
            Margin=GlobalScale * 0.05)
        return rend.draw(graph, pos, 
                size=('600px', '600px'))

    nx.Graph._repr_svg_ = getsvg
    
install_repr_svg()

if __name__ == "__main__":
    from sys import argv
    if len(argv) > 1 and argv[1] == 'mpl':
        testmpl()
    else:
        test()
