import sys
import subprocess

# This script ensures consistent width variations and centers glyphs
# within their bounding boxes across all weights.

# Configuration
WIDTH_MULTIPLIER = 0.85  # Adjust this to make all glyphs wider/narrower

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
hvar_table = font["HVAR"] if "HVAR" in font else None  # Horizontal metrics variations
fvar_table = font["fvar"] if "fvar" in font else None  # Font variations table

# Characters to adjust
tabular_chars = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", ",", ".", "$", "(", ")"]

# Map to glyph names
cmap = font["cmap"].getcmap(3, 1).cmap  # Windows Unicode cmap
char_glyphs = {char: cmap[ord(char)] for char in tabular_chars if ord(char) in cmap}

# First pass: find the widest character and its variation pattern
max_width = 0
max_width_glyph = None
width_variations = None

for char, glyph_name in char_glyphs.items():
    if glyph_name in hmtx_table.metrics:
        width, _ = hmtx_table.metrics[glyph_name]
        if width > max_width:
            max_width = width
            max_width_glyph = glyph_name

# Get the variation pattern from the widest glyph
if (hvar_table and hasattr(hvar_table, 'table') and
    hasattr(hvar_table.table, 'VarStore')):
    var_store = hvar_table.table.VarStore
    if hasattr(var_store.VarData[0], 'Item'):
        width_variations = list(var_store.VarData[0].Item[0])

# Apply width multiplier
max_width = int(max_width * WIDTH_MULTIPLIER)
print(f"Using maximum width of {max_width} units (after {WIDTH_MULTIPLIER}x multiplier)")

# Second pass: set all characters to the maximum width and center them
for char, glyph_name in char_glyphs.items():
    if glyph_name in hmtx_table.metrics:
        current_width, current_lsb = hmtx_table.metrics[glyph_name]

        # Get glyph bounding box from glyf table if available
        if 'glyf' in font and glyph_name in font['glyf']:
            glyph = font['glyf'][glyph_name]
            if not glyph.isComposite():
                # Calculate actual glyph width using xMin and xMax
                actual_width = glyph.xMax - glyph.xMin
                # Center the glyph by adjusting the LSB
                new_lsb = (max_width - actual_width) // 2
                # Set the new width and centered LSB
                hmtx_table.metrics[glyph_name] = (max_width, new_lsb)
        else:
            # For composite glyphs or CFF fonts, maintain current LSB
            hmtx_table.metrics[glyph_name] = (max_width, current_lsb)

        # Remove any width variations in HVAR
        if (hvar_table and hasattr(hvar_table, 'table') and
            hasattr(hvar_table.table, 'AdvWidthMap') and
            hvar_table.table.AdvWidthMap is not None):
            if hasattr(font, 'getGlyphID'):
                glyph_id = font.getGlyphID(glyph_name)
                if glyph_id in hvar_table.table.AdvWidthMap:
                    # Remove width variations by setting mapping to None
                    hvar_table.table.AdvWidthMap[glyph_id] = None

# Special handling for parentheses
if "(" in char_glyphs and ")" in char_glyphs:
    paren_left = char_glyphs["("]
    paren_right = char_glyphs[")"]

    # For parentheses, we want them tucked in, so we'll use zero width
    # and position them with LSB like before, but handle weight variations
    hmtx_table.metrics[paren_left] = (0, -280)
    hmtx_table.metrics[paren_right] = (0, -90)

    # Clear width variations for parentheses in VarStore
    if (hvar_table and hasattr(hvar_table, 'table') and
        hasattr(hvar_table.table, 'VarStore')):
        var_store = hvar_table.table.VarStore

        # Reset all variation data for parentheses
        for var_data in var_store.VarData:
            if hasattr(var_data, 'Item'):
                for item in var_data.Item:
                    # Set all deltas to 0
                    item.clear()

# Save modified font
font.save(OUTPUT_FONT)

print(f"✅ Saved tabular version as {OUTPUT_FONT}")
print(f"Note: Width variations are now consistent and glyphs are centered. Adjust WIDTH_MULTIPLIER in the script to change overall width.")
