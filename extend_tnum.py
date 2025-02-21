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
from fontTools.feaLib.builder import addOpenTypeFeaturesFromString

# Input and output file names
INPUT_FONT = "GeneralSans-Variable.ttf"
OUTPUT_FONT = "GeneralSans-Variable-Extended.ttf"

# Load font
font = TTFont(INPUT_FONT)

# Define tabular width
TABULAR_WIDTH = 580

# Characters to adjust
tabular_chars = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", ".", "$", "(", ")"]

# Map Unicode characters to glyph names
cmap = font["cmap"].getcmap(3, 1).cmap  # Windows Unicode cmap
char_glyphs = {char: cmap[ord(char)] for char in tabular_chars if ord(char) in cmap}

# Get font tables
hmtx_table = font["hmtx"]
glyf_table = font["glyf"] if "glyf" in font else None  # Only for static TTFs
gvar_table = font["gvar"] if "gvar" in font else None  # For variable fonts

# Ensure new glyphs exist and are registered
new_glyphs = []  # Store newly added glyphs
glyph_order = font.getGlyphOrder()  # Existing glyph order

for char, glyph_name in char_glyphs.items():
    new_glyph_name = glyph_name + ".tnum"

    if new_glyph_name not in glyph_order:
        # Duplicate the glyph in glyf table (for static fonts)
        if glyf_table and glyph_name in glyf_table.glyphs:
            font["glyf"].glyphs[new_glyph_name] = font["glyf"].glyphs[glyph_name]

        # Duplicate glyph metrics
        if glyph_name in hmtx_table.metrics:
            original_width, original_lsb = hmtx_table.metrics[glyph_name]
            hmtx_table.metrics[new_glyph_name] = (TABULAR_WIDTH, (TABULAR_WIDTH - original_width) // 2)

        # Register in glyph order
        glyph_order.append(new_glyph_name)
        new_glyphs.append(new_glyph_name)

        # Handle variable fonts: Copy glyph variation data
        if gvar_table and glyph_name in gvar_table.variations:
            gvar_table.variations[new_glyph_name] = gvar_table.variations[glyph_name]

# Update the glyph order in the font
font.setGlyphOrder(glyph_order)

# Ensure all `.tnum` glyphs exist before applying `tnum`
missing_glyphs = [g for g in new_glyphs if g not in font.getGlyphOrder()]
if missing_glyphs:
    print(f"❌ Error: These glyphs are missing: {missing_glyphs}")
    sys.exit(1)

# Add OpenType `tnum` feature
fea_code = "\nfeature tnum {\n"
for char, glyph_name in char_glyphs.items():
    tnum_glyph = glyph_name + ".tnum"
    if tnum_glyph in font.getGlyphOrder():
        fea_code += f"    sub {glyph_name} by {tnum_glyph};\n"
fea_code += "} tnum;\n"

# Apply OpenType feature
addOpenTypeFeaturesFromString(font, fea_code)

# Save modified font
font.save(OUTPUT_FONT)

print(f"✅ Fixed `tnum` support saved as {OUTPUT_FONT}")
