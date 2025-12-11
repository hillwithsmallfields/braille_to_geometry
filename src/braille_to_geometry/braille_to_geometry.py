import math
import shapely

DOTS = {
    "A": 0b000001,
    "B": 0b000011,
    "C": 0b001001,
    "D": 0b011001,
    "E": 0b010001,
    "F": 0b001011,
    "G": 0b011011,
    "H": 0b010011,
    "I": 0b001010,
    "J": 0b011010,
    "K": 0b000101,
    "L": 0b000111,
    "M": 0b001101,
    "N": 0b011101,
    "O": 0b010101,
    "P": 0b001111,
    "Q": 0b011111,
    "R": 0b010111,
    "S": 0b001110,
    "T": 0b011110,
    "U": 0b100101,
    "V": 0b100111,
    "W": 0b111010,
    "X": 0b101101,
    "Y": 0b111101,
    "Z": 0b110101,
}

MORE_DOTS = {
    "Á": 0b000001,
    "À": 0b000001,
    "Ä": 0b000001,
    "É": 0b010001,
    "È": 0b010001,
    "Ë": 0b010001,
    "Í": 0b010101,
    "Ì": 0b010101,
    "Ï": 0b010101,
    "Ó": 0b001010,
    "Ò": 0b001010,
    "Ö": 0b001010,
    "Ú": 0b100101,
    "Ù": 0b100101,
    "Ü": 0b100101,
}

class DotShape:

    """Parent class for things that return dot shapes.

    They are made as classes with a common parent, so that we can test
    unambiguously for one of them being passed in as the dot specification.
    """

    def __init__(self):
        self._dot = None

    def dot(self):
        return self._dot

class Square(DotShape):

    def __init__(self, size):
        self._dot =  shapely.Polygon([[0, 0],
                                      [0, size],
                                      [size, size],
                                      [size, 0]])

class Diamond(DotShape):

    def __init__(self, size):
        half = size/2
        self._dot =  shapely.Polygon([[-half, 0],
                                      [0, half],
                                      [half, 0],
                                      [0, -half]])

class Octagon(DotShape):

    def __init__(self, size):
        half = size/2
        octant = math.sqrt(half/2)
        self._dot =  shapely.Polygon([[-half, 0],
                                      [-octant, octant],
                                      [0, half],
                                      [octant, octant],
                                      [half, 0],
                                      [octant, -octant],
                                      [0, -half],
                                      [-octant, -octant]])

class BrailleDotter:

    def __init__(self, dot_spacing, cell_x_size, cell_y_size,
                 dot_size=None,
                 crush_diacritics=True,
                 dot_shape=None,
                 scale=1.0
                 ):
        self.dot_size = dot_size
        self.scale = scale
        self.dot_spacing = dot_spacing
        self.cell_x_size = cell_x_size
        self.cell_y_size = cell_y_size
        self.dots = (DOTS | MORE_DOTS) if crush_diacritics else DOTS
        self.dot_shape = ((dot_shape(self.dot_size).dot()
                           if isinstance(dot_shape, type) and issubclass(dot_shape, DotShape)
                           else dot_shape)
                          if dot_shape
                          else shapely.buffer(shapely.Point(0, 0),
                                              ((self.dot_size/2)
                                                      if self.dot_size
                                                      else (self.dot_size/8))))
        print("dot shape", dot_shape, isinstance(dot_shape, type) and issubclass(dot_shape, DotShape), "makes dot", self.dot_shape)

    def text_to_dots(self, text, dot_size=None):
        """Convert a string to a shapely.GeometryCollection of Braille dots.

        Currently handles only letters, spaces and newlines."""
        result = []
        # move the dot centres in to allow for the size of the dot
        margin = self.dot_size or cell_x_size / 4
        x = margin
        y = margin
        for character in text:
            match character:
                case '\n':
                    x = margin
                    y += self.cell_y_size * self.scale
                case ' ':
                    x += self.cell_x_size * self.scale
                case _:
                    if character.isalpha():
                        dots = self.dots.get(character.upper())
                        if dots:
                            for i in range(6):
                                if dots & 1:
                                    result.append(
                                        shapely.affinity.translate(
                                            self.dot_shape,
                                            x + self.dot_spacing*(i//3)*self.scale,
                                            y + self.dot_spacing*(i%3)*self.scale))
                                dots >>= 1
                        x += self.cell_x_size * self.scale
        return shapely.GeometryCollection(result)

    def text_to_bbox(self, text, dot_size=None):
        """Return the bounding box of a string, as a shapely.Polygon.

        This can be used to find whether a braille label can be placed
        in a given position without interfering with other geometry.
        """
        column = 0
        max_column = 0
        rows = 1
        for character in text:
            if character == '\n':
                rows += 1
                if column > max_column:
                    max_column = column
                column = 0
            else:
                column += 1
        if column > max_column:
            max_column = column
        right = max_column * self.cell_x_size * self.scale
        bottom = rows * self.cell_y_size * self.scale
        return shapely.Polygon([[0, 0], [right, 0], [right, bottom], [0, bottom]])

    def text_dimensions(self, text, dot_size=None):
        """Return the width and height of a brailled string."""
        column = 0
        max_column = 0
        rows = 1
        for character in text:
            if character == '\n':
                rows += 1
                if column > max_column:
                    max_column = column
                column = 0
            else:
                column += 1
        if column > max_column:
            max_column = column
        return max_column * self.cell_x_size, rows * self.cell_y_size

class BrailleDotterUKAAF(BrailleDotter):

    """Braille dotter using the dimensions from the UK Association for Accessible Formats.

    This is the same as the Marburg Medium Braille font as mandated
    for pharmaceutical braille in the EU.
    """

    def __init__(self, **kwargs):
        print("making BrailleDotterUKAAF with kwargs", kwargs)

        super().__init__(
            **({
                # Dimensions from
                # https://www.ukaaf.org/wp-content/uploads/2020/03/Braille-Standard-Dimensions.pdf,
                # in mm
                'dot_size': 1.5,
                'dot_spacing': 2.5,
                'cell_x_size': 6.0,
                'cell_y_size': 10.0,
            } | kwargs))

class BrailleDotterBANA(BrailleDotter):

    """Braille dotter using the dimensions from the Braille Authority of North America."""

    def __init__(self, **kwargs):
        super().__init__(
            **({
                # Dimensions from
                # https://brailleauthority.org/size-and-spacing-braille-characters
                # in mm
                'dot_size': 1.44,
                'dot_spacing': 2.34,
                'cell_x_size': 6.2,
                'cell_y_size': 10.0,
            } | kwargs))

with open("/tmp/dots.svg", 'w') as outstream:
    text = "Braille in\ntwo lines"
    dotter = BrailleDotterUKAAF()
    outstream.write('<svg width="600" height="600">\n')
    outstream.write(dotter.text_to_bbox(text).svg())
    outstream.write(dotter.text_to_dots(text).svg())
    outstream.write('</svg>')
