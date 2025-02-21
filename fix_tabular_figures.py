import sys
import subprocess

# Ensure dependencies are installed
REQUIRED_PACKAGES = ["fonttools"]

for package in REQUIRED_PACKAGES:
    try:
        __import__(package)
    except ImportError:
        print(f"📦 Installing missing package: {package}")
        subprocess.check_call([sys.executable, "-m", "pip", "install", package])

from fontTools.ttLib import TTFont

# Input and output file names
INPUT_FONT = "GeneralSans-Variable.ttf"
OUTPUT_FONT = "GeneralSans-Variable-Tabular.ttf"

# Load font
font = TTFont(INPUT_FONT)

# Get font tables
hmtx_table = font["hmtx"]
glyf_table = font["glyf"] if "glyf" in font else None  # Only present in TTFs
gvar_table = font["gvar"] if "gvar" in font else None  # Present in variable fonts

# Define tabular width
TABULAR_WIDTH = 580

# Characters to adjust
tabular_chars = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", ".", "$", "(", ")"]

# Map to glyph names
cmap = font["cmap"].getcmap(3, 1).cmap  # Windows Unicode cmap
char_glyphs = {char: cmap[ord(char)] for char in tabular_chars if ord(char) in cmap}

# Adjust all tabular characters
for char, glyph_name in char_glyphs.items():
    if glyph_name in hmtx_table.metrics:
        # Get existing width and left side bearing
        old_width, old_lsb = hmtx_table.metrics[glyph_name]

        # Compute new left-side bearing to center the glyph
        new_lsb = (TABULAR_WIDTH - old_width) // 2

        # Apply new metrics
        hmtx_table.metrics[glyph_name] = (TABULAR_WIDTH, new_lsb)

    # Adjust glyph outlines for static TTFs
    if glyf_table and glyph_name in glyf_table:
        glyph = glyf_table[glyph_name]
        if not glyph.isComposite():
            shift = (TABULAR_WIDTH - (glyph.xMax - glyph.xMin)) // 2
            glyph.xMin += shift
            glyph.xMax += shift

    # Adjust variable font deltas if needed
    if gvar_table and glyph_name in gvar_table.variations:
        for var in gvar_table.variations[glyph_name]:
            if "XAdv" in var.coordinates:
                var.coordinates["XAdv"] = TABULAR_WIDTH

# Handle special parentheses alignment for negative values
if "(" in char_glyphs and ")" in char_glyphs:
    paren_left = char_glyphs["("]
    paren_right = char_glyphs[")"]

    # Apply negative left-side bearings and set width to 0
    # Adjust as needed for proper tuck-in effect
    hmtx_table.metrics[paren_left] = (0, -280)
    hmtx_table.metrics[paren_right] = (0, -90)

# Save modified font
font.save(OUTPUT_FONT)

print(f"✅ Saved tabular version as {OUTPUT_FONT}")
