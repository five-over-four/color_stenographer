from PIL import Image
from random import choice
import argparse
# import base64

#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #
# Define basic bin -> ascii and ascii -> bin functions here. #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #    #

def to_bin(s: str):
    """
    Returns a string of bytes from a string of text;
    "hello" => "0110100001100101011011000110110001101111"
    """
    return "".join([ str(bin(ord(char)))[2:].zfill(8) for char in s])

def to_ascii(b: str):
    """
    Returns a string of characters from a string of bytes:
    "0110100001100101011011000110110001101111" => "hello"
    """
    pos = 0
    s = ""
    while pos * 8 < len(b):
        s += decode_byte(b[pos * 8:pos * 8 + 8])
        pos += 1
    return s

def decode_byte(b: str) -> str:
    """
    Returns string representation of a byte into a character:
    "11000001" => "a"
    """
    return chr(int(bytes(b, "utf-8"), 2))

#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #
# Actual image encodings and decodings here.                #
#   #   #   #   #   #   #   #   #   #   #   #   #   #   #   #

channels = {"red": 0, "green": 1, "blue": 2}

def encode_message(img, msg):
    """
    writes an ascii message (msg) into the colour channels
    of your chosen image as a sequence of 1s and 0s.
    Sequence: first red, then green, then blue.
    """
    write_binary_data(img, to_bin(msg))

def decode_message(img):
    """
    Reads a potential message encoded by this program from
    an image file (img), hidden in the colour channels.
    A message begins with 24 0s and ends with 24 0s in a row.
    """
    return to_ascii(get_binary_data(img))

def get_binary_data(img):
    """
    Reads ch channels' parity as 0 or 1 into b and returns.
    Terminates on 24 bits of "10101010..."
    """
    b = ""
    key_seq = "10"*12
    for ch in ("red", "green", "blue"):
        for x in range(width):
            for y in range(height):
                b += str(img[x, y][channels[ch]] % 2)
                if width * y + x == 24 and b[:24] != key_seq:
                    return to_bin("no message found!")
    try:
        endpoint = b[24:].index(key_seq) + 24
        return b[24: endpoint] # cut out everything outside key_seq
    except Exception: # the image was too small to contain the key_seq at the end.
        return b[24:]

def write_binary_data(img, msg):
    """
    Writes an already encoded string of bytes into the pixels of
    the chosen image from a given message. msg is a sequence
    of 1s and 0s.
    """
    # message ends and starts with 24 bits of alternating 1s and 0s.
    msg = "10"*12 + msg + "10"*12
    msg_pos = 0
    for ch in ("red", "green", "blue"): # start with red, fill other channels as needed.
        for x in range(width):
            for y in range(height):
                if msg_pos >= len(msg):
                    return 1
                if msg[msg_pos] == "0":
                    img[x, y] = replace_pixel(img[x, y], round_even(img[x, y][channels[ch]]), ch)
                else:
                    img[x, y] = replace_pixel(img[x, y], round_odd(img[x, y][channels[ch]]), ch)
                msg_pos += 1

def round_even(n):
    """
    Rounds an integer to a near even number.
    """
    if n == 255:
        return 254
    return n if (n % 2 == 0) else n + choice([-1,1])

def round_odd(n):
    """
    Rounds an integer to near odd number.
    """
    if n == 0:
        return 1
    return n if (n % 2 == 1) else n + choice([-1,1])

# this is really clumsy and slow.
def replace_pixel(pixel, new_val, ch):
    """
    Returns a pixel 3-tuple (r,g,b), where the ch-corresponding
    colour is replaced by new_val.
    """
    r, g, b = pixel
    if ch == "red":
        return (new_val, g, b)
    elif ch == "green":
        return (r, new_val, b)
    else:
        return (r, g, new_val)
    
def analyze_file(img):
    """
    Gives some heuristic constraints for how much data can be encoded
    within the image file.
    """
    from math import floor
    from decimal import Decimal, ROUND_UP

    max_size = floor(width*height*3/8)-24

    # Python rounds 7.955 to 7.95 instead of 7.96.
    def round_proper(val):
        return Decimal(str(val)).quantize(Decimal('.01'), rounding=ROUND_UP)
    
    return f"The image resolution is {width} x {height}.\n" \
            f"Maximum stored characters: {max_size} or {round_proper(max_size/1000)}kB\n" \
            f"Roughly {floor(max_size/6)} words or {round_proper(max_size/(6*280))} pages for a book with 280 words per page."


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
                    prog="Simple Binary Steganography Tool", 
                    description="Encode and decode a message into and from the colour channels\nof an image.",
                    epilog="")
    
    parser.add_argument("filename", help="name of the image file.")
    parser.add_argument("-i", "--input", metavar="TEXTFILE", help="encode the contents of a text file into the image.")
    parser.add_argument("-e", "--encode", metavar="MESSAGE", nargs=1, help="encode a message into the image file.")
    parser.add_argument("-d", "--decode", action="store_true", help="read a message from the image file.")
    parser.add_argument("-a", "--analyze", action="store_true", help="gives storage constraints for the image.")
    args = parser.parse_args()
    
    image = Image.open(args.filename).convert("RGB")
    img = image.load()
    width, height = image.size

    if args.decode:
        print(decode_message(img))
    elif args.input:
        text = open(args.input, "r").read()
        stripped = "".join((c for c in text if 0 < ord(c) < 255)) # stupid unicode.
        encode_message(img, stripped)
        image.save("encoded.png")
    elif args.encode:
        encode_message(img, args.encode)
        image.save("encoded.png")
    elif args.analyze:
        print(analyze_file(img))