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

class BrailleDotter:

    def __init__(self, dot_spacing, cell_x_size, cell_y_size, dot_size):
        self.dot_size = dot_size
        self.dot_spacing = dot_spacing
        self.cell_x_size = cell_x_size
        self.cell_y_size = cell_y_size

    def text_to_dots(self, text, dot_size=None):
        """Convert a string to a shapely.GeometryCollection of Braille dots.

        Currently handles only letters, spaces and newlines."""
        result = []
        x = 0
        y = 0
        for character in text:
            match character:
                case '\n':
                    x = 0
                    y += self.cell_y_size
                case ' ':
                    x += self.cell_x_size
                case _:
                    if character.isalpha():
                        dots = DOTS.get(character.upper())
                        if dots:
                            for i in range(6):
                                if dots & 1:
                                    result.append(shapely.buffer(shapely.Point(x+self.dot_spacing*(i//3),
                                                                               y+self.dot_spacing*(i%3)),
                                                                 ((dot_size/2)
                                                                  if dot_size
                                                                  else (self.dot_size/8))))

                                dots >>= 1
                        x += self.cell_x_size
        return shapely.GeometryCollection(result)

class BrailleDotterUKAAF(BrailleDotter):

    """Braille dotter using the dimensions from the UK Association for Accessible Formats.

    This is the same as the Marburg Medium Braille font as mandated
    for pharmaceutical braille in the EU.
    """

    def __init__(self):
        super().__init__(
            # Dimensions from
            # https://www.ukaaf.org/wp-content/uploads/2020/03/Braille-Standard-Dimensions.pdf,
            # in mm
            dot_size=1.5,
            dot_spacing=2.5,
            cell_x_size=6.0,
            cell_y_size=10.0,
        )

class BrailleDotterBANA(BrailleDotter):

    """Braille dotter using the dimensions from the Braille Authority of North America."""

    def __init__(self):
        super().__init__(
            # Dimensions from
            # https://brailleauthority.org/size-and-spacing-braille-characters
            # in mm
            dot_size=1.44,
            dot_spacing=2.34,
            cell_x_size=6.2,
            cell_y_size=10.0,
        )

with open("/tmp/dots.svg", 'w') as outstream:
    outstream.write('<svg width="600" height="600">\n')
    outstream.write(BrailleDotterUKAAF().text_to_dots("Braille in\ntwo lines").svg())
    outstream.write('</svg>')
