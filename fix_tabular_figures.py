import sys
import subprocess

# This script ensures consistent width variations and centers glyphs
# within their bounding boxes across all weights.

# Configuration
WIDTH_MULTIPLIER = 0.9  # Increased to avoid negative space

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

# Characters to adjust
tabular_chars = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "$", "(", ")"]

# Map to glyph names
cmap = font["cmap"].getcmap(3, 1).cmap  # Windows Unicode cmap
char_glyphs = {char: cmap[ord(char)] for char in tabular_chars if ord(char) in cmap}

def collect_metrics(font, char_glyphs):
    metrics = {}
    for char, glyph_name in char_glyphs.items():
        metrics[char] = {'glyph_name': glyph_name}
        if glyph_name in font['hmtx'].metrics:
            width, lsb = font['hmtx'].metrics[glyph_name]
            glyph = font['glyf'][glyph_name]

            # Basic metrics
            metrics[char].update({
                'width': width,
                'lsb': lsb,
                'xMin': glyph.xMin,
                'xMax': glyph.xMax,
                'actual_width': glyph.xMax - glyph.xMin
            })

            # Vertical metrics if available
            if 'vmtx' in font:
                vwidth, tsb = font['vmtx'].metrics.get(glyph_name, (0, 0))
                metrics[char].update({
                    'vwidth': vwidth,
                    'tsb': tsb,
                    'yMin': glyph.yMin,
                    'yMax': glyph.yMax
                })

            # Check for variation data
            if 'GDEF' in font:
                gdef = font['GDEF'].table
                if hasattr(gdef, 'VarStore'):
                    metrics[char]['has_variations'] = True

            # Check for kerning in GPOS
            if 'GPOS' in font:
                gpos = font['GPOS'].table
                has_kerning = any(
                    lookup.LookupType == 2  # Type 2 is pair adjustment
                    for lookup in gpos.LookupList.Lookup
                    if hasattr(lookup, 'LookupType')
                )
                metrics[char]['has_kerning'] = has_kerning
    return metrics

# Create debug tables for metrics
def print_metrics_table(title, font, char_glyphs):
    metrics = collect_metrics(font, char_glyphs)
    print(f"\n{title}")
    print("-" * 120)
    print(f"{'Character':<10} {'Glyph Name':<15} {'Width':>8} {'LSB':>6} {'xMin':>6} {'xMax':>6} {'yMin':>6} {'yMax':>6} {'V.Width':>8} {'TSB':>6} {'Var':>5} {'Kern':>5}")
    print("-" * 120)
    for char, data in sorted(metrics.items()):
        print(f"{char:<10} {data['glyph_name']:<15} ", end='')
        print(f"{data.get('width', 0):>8} {data.get('lsb', 0):>6} {data.get('xMin', 0):>6} {data.get('xMax', 0):>6} ", end='')
        print(f"{data.get('yMin', 0):>6} {data.get('yMax', 0):>6} {data.get('vwidth', 0):>8} {data.get('tsb', 0):>6} ", end='')
        print(f"{'*' if data.get('has_variations', False) else ' ':>5} {'*' if data.get('has_kerning', False) else ' ':>5}")
    return metrics

# Collect and print original metrics
original_metrics = print_metrics_table("Original Metrics", font, char_glyphs)

# First pass: find the widest character
max_width = 0
for char, glyph_name in char_glyphs.items():
    if glyph_name in hmtx_table.metrics:
        width, _ = hmtx_table.metrics[glyph_name]
        if width > max_width:
            max_width = width

# Apply width multiplier
max_width = int(max_width * WIDTH_MULTIPLIER)
print(f"Using maximum width of {max_width} units (after {WIDTH_MULTIPLIER}x multiplier)")

# Second pass: set all characters to the maximum width and center glyphs
for char, glyph_name in char_glyphs.items():
    if glyph_name in hmtx_table.metrics and char not in ['(', ')']:
        glyph = font['glyf'][glyph_name]

        # Calculate the actual glyph width
        glyph_width = glyph.xMax - glyph.xMin

        # Calculate centering offset
        padding = max_width - glyph_width
        left_padding = padding // 2

        # Calculate the shift needed to center the glyph
        shift = left_padding - glyph.xMin

        # Shift all coordinates to center the glyph
        if hasattr(glyph, 'coordinates'):
            for i in range(len(glyph.coordinates)):
                x, y = glyph.coordinates[i]
                glyph.coordinates[i] = (x + shift, y)

        # Update the glyph bounds
        glyph.xMax = glyph.xMax + shift
        glyph.xMin = glyph.xMin + shift

        # Set the new width
        hmtx_table.metrics[glyph_name] = (max_width, left_padding)

        # Clear variation data for this glyph if GDEF table exists
        if 'GDEF' in font and hasattr(font['GDEF'].table, 'VarStore'):
            var_store = font['GDEF'].table.VarStore
            for var_data in var_store.VarData:
                if hasattr(var_data, 'Item'):
                    for item in var_data.Item:
                        if glyph_name in item:
                            item.clear()

        # Remove kerning for this glyph if GPOS table exists
        if 'GPOS' in font:
            gpos = font['GPOS'].table
            for lookup in gpos.LookupList.Lookup:
                if hasattr(lookup, 'LookupType') and lookup.LookupType == 2:  # Type 2 is pair adjustment
                    for subtable in lookup.SubTable:
                        if hasattr(subtable, 'Coverage') and glyph_name in subtable.Coverage.glyphs:
                            subtable.Coverage.glyphs.remove(glyph_name)

# Special handling for parentheses
if "(" in char_glyphs and ")" in char_glyphs:
    paren_left = char_glyphs["("]
    paren_right = char_glyphs[")"]

    # For parentheses, we want them tucked in with zero width
    hmtx_table.metrics[paren_left] = (0, -280)
    hmtx_table.metrics[paren_right] = (0, -90)

# Clear width variations in HVAR for tabular characters
if (hvar_table and hasattr(hvar_table, 'table') and
    hasattr(hvar_table.table, 'VarStore')):
    var_store = hvar_table.table.VarStore

    # For each variation region
    for var_data in var_store.VarData:
        if hasattr(var_data, 'Item'):
            # For each glyph's variation data
            for i, item in enumerate(var_data.Item):
                # Check if this variation data corresponds to any of our tabular glyphs
                for glyph_name in char_glyphs.values():
                    if font.getGlyphID(glyph_name) == i:
                        # Zero out all variations for this glyph
                        var_data.Item[i] = [0] * len(item)

# Save modified font
font.save(OUTPUT_FONT)

# Load modified font and print final metrics
font_after = TTFont(OUTPUT_FONT)
final_metrics = print_metrics_table("Final Metrics", font_after, char_glyphs)

print(f"\n✅ Saved tabular version as {OUTPUT_FONT}")
print(f"Note: Width variations are now consistent with LSB at 0. Adjust WIDTH_MULTIPLIER in the script to change overall width.")
