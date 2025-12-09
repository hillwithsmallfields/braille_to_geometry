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

# Dimensions from https://www.ukaaf.org/wp-content/uploads/2020/03/Braille-Standard-Dimensions.pdf, in mm
DOT_SIZE = 1.5
DOT_SPACING = 2.5
CELL_X_SIZE = 6.0
CELL_Y_SIZE = 10.0

def text_to_dots(text):
    result = []
    x = 0
    y = 0
    for character in text:
        match character:
            case '\n':
                x = 0
                y += CELL_Y_SIZE
            case ' ':
                x += CELL_X_SIZE
            case _:
                if character.isalpha():
                    dots = DOTS.get(character.upper())
                    if dots:
                        for i in range(6):
                            if dots & 1:
                                result.append(shapely.buffer(shapely.Point(x+DOT_SPACING*(i//3),
                                                                           y+DOT_SPACING*(i%3)),
                                                             DOT_SIZE/8))

                            dots >>= 1
                    x += CELL_X_SIZE
    return shapely.GeometryCollection(result)

with open("/tmp/dots.svg", 'w') as outstream:
    outstream.write('<svg width="600" height="600">\n')
    outstream.write(text_to_dots("Braille in\ntwo lines").svg())
    outstream.write('</svg>')
