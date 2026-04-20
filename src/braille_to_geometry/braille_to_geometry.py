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

class GeometricOutput:

    """Parent class for geometric output systems."""

    def __init__(self):
        self.translate = None
        self.combine = None
        self.difference = None

class GeometricOutput_2d(GeometricOutput):

    def __init__(self):
        self.translate = shapely.affinity.translate
        self.combine = shapely.GeometryCollection
        self.difference = shapely.difference

class GeometricOutput_3d(GeometricOutput):

    pass

class DotShape:

    """Parent class for things that return dot shapes.

    They are made as classes with a common parent, so that we can test
    unambiguously for one of them being passed in as the dot specification.
    """

    def __init__(self):
        self._dot_2d = None
        self._dot_3d = None

    def dot_2d(self):
        return self._dot_2d

    def dot_3d(self):
        return self._dot_3d

class Square(DotShape):

    def __init__(self, size):
        self._dot_2d =  shapely.Polygon([[0, 0],
                                         [0, size],
                                         [size, size],
                                         [size, 0]])

class Diamond(DotShape):

    def __init__(self, size):
        half = size/2
        self._dot_2d =  shapely.Polygon([[-half, 0],
                                         [0, half],
                                         [half, 0],
                                         [0, -half]])

class Octagon(DotShape):

    def __init__(self, size):
        half = size/2
        octant = math.sqrt(half/2)
        self._dot_2d =  shapely.Polygon([[-half, 0],
                                         [-octant, octant],
                                         [0, half],
                                         [octant, octant],
                                         [half, 0],
                                         [octant, -octant],
                                         [0, -half],
                                         [-octant, -octant]])

class Circle(DotShape):

    def __init__(self, size):
        self._dot_3d = "sphere(%d);" % size

class BrailleDotter:

    def __init__(self, dot_spacing, cell_x_size, cell_y_size,
                 dot_size=None,
                 crush_diacritics=True,
                 dot_shape_2d=None,
                 dot_shape_3d=None,
                 scale=1.0,
                 y_scale_adjust=1.0
                 geometric_output=GeometricOutput_2d,
                 ):
        self.dot_size = dot_size
        self.scale = scale
        self.y_scale_adjust = y_scale_adjust
        self.dot_spacing = dot_spacing
        self.cell_x_size = cell_x_size
        self.cell_y_size = cell_y_size
        self.dots = (DOTS | MORE_DOTS) if crush_diacritics else DOTS
        self.dot_shape_2d = ((dot_shape_2d(self.dot_size).dot_2d()
                              if isinstance(dot_shape_2d, type) and issubclass(dot_shape_2d, DotShape)
                              else dot_shape_2d)
                             if dot_shape_2d
                             else shapely.buffer(shapely.Point(0, 0),
                                                 ((self.dot_size/2)
                                                  if self.dot_size
                                                  else (self.dot_size/8))))
        self.dot_shape_3d = ((dot_shape_3d(self.dot_size).dot_3d()
                              if isinstance(dot_shape_3d, type) and issubclass(dot_shape_3d, DotShape)
                              else dot_shape_3d)
                             if dot_shape_3d
                             else "sphere(1);")
        self.geometric_output = geometric_output

    def text_to_dots(self, text, dot_size=None):
        """Convert a string to a shapely.GeometryCollection of Braille dots.

        Currently handles only letters, spaces and newlines."""
        result = []
        # move the dot centres in to allow for the size of the dot
        margin = self.dot_size or self.cell_x_size / 4
        margin = self.cell_x_size / 4
        x = margin
        y = margin
        x_scale = self.scale
        y_scale = self.scale * self.y_scale_adjust
        for character in text:
            match character:
                case '\n':
                    x = margin
                    y += self.cell_y_size * y_scale
                case ' ':
                    x += self.cell_x_size * x_scale
                case _:
                    if character.isalpha():
                        dots = self.dots.get(character.upper())
                        if dots:
                            for i in range(6):
                                if dots & 1:
                                    result.append(
                                        self.geometric_output.translate(
                                            self.dot_shape_2d,
                                            x + self.dot_spacing*(i//3)*x_scale,
                                            y + self.dot_spacing*(i%3)*y_scale))
                                dots >>= 1
                    elif ord(character) & 0xff00 == 0x2800:
                        for i in range(6):
                            if dots & 1:
                                result.append(
                                    self.geometric_output.translate(
                                        self.dot_shape_2d,
                                        x + self.dot_spacing*(i//3)*x_scale,
                                        y + self.dot_spacing*(i%3)*y_scale))
                            dots >>= 1
                    x += self.cell_x_size * x_scale

        return self.geometric_output.combine(result)

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
        # move the dot centres in to allow for the size of the dot
        margin = self.dot_size or cell_x_size / 4
        right = max_column * self.cell_x_size * self.scale + margin*2
        bottom = rows * self.cell_y_size * self.scale + margin*2
        return shapely.Polygon([[0, 0], [right, 0], [right, bottom], [0, bottom]])

    def text_in_box(self, text, dot_size=None):
        """Convert a string to a collection of Braille dots, against an incised background."""
        return self.geometric_output.difference(self.text_to_bbox(text, dot_size=dot_size),
                                                self.text_to_dots(text, dot_size=dot_size))

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
                # 'dot_size': 1.5,
                'dot_size': 1,
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
    text = "Braille in several\nlines or rows of\nbraille cells for\ntesting purposes"
    dotter = BrailleDotterUKAAF()
    outstream.write('<svg width="600" height="600">\n')
    # outstream.write(dotter.text_to_bbox(text).svg())
    # outstream.write(dotter.text_to_dots(text).svg())
    outstream.write(dotter.text_in_box(text).svg())
    outstream.write('</svg>')
