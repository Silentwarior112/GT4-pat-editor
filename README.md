# GT4-pat-editor
Basic python scripts that modify the color patch files in Gran Turismo 4, which allow for custom colors on certain cars.

Current tooling is crude and unfinished, and practical applications will require some manual hex editing.

Credit goes to Nenkai for file format research and figuring.
https://github.com/Nenkai/GT-File-Specifications-Documentation

To do:
- Integrate both scripts into one
- Automate remaining processes that currently require manual hex editing

How to use:

1. Extract the .pat file from the Menu model and save to a separate file.
Using a hex editor, check offset 1C-1F to get the starting offset of the .pat file.
Then, check offset 20-23 to get the starting offset of the next file.
This is the general byte range of the pat file, so copy that binary data and save it to a separate file.
Make sure not to copy the padding bytes at the end of the pat file.

2. Using the color adder script, add additional color entries to the pat file and save.
Take note of the size difference of the Menu pat file, as in the tool's current implementation,
manual hex editing is needed to update the offsets in the menu model. The Lod model does not need this.
Do this for both the menu pat, and the lod/open pat.

4. Next, open the color editor. Select one of the paint tabs, and export
it to a PNG. You will want to also export a different paint as well, so that you
can compare the difference between them, so that you will know which pixels to modify.

When choosing which color to use as the baseline color for modification, it's best to use white, or whatever the brightest color in the set is.
For determining which pixels are the right ones,
it's best to compare two colors that are not shades.
For example, green and blue.

5. Open the PNGs in an image editor, and splice the strips together.
Pick one of strips to modify.
Take the selection tool on add mode, and
select each pixel in the strip that is different
in hue to the other strip.
Once they are all selected, apply your desired adjustments/effects.
Really though, the only practical adjustment is the Hue.
Brightness can't be modified, as this will mess up the shading.
Most obvious example is the door handle of the car.
Once the strip is modified, get rid of the comparison strip and
then save the new png.

6. Go back to the color editor, and import your PNG strip into whichever paint tab you want to overwrite, then save.
This should be the new one that you added in the previous step, but you can also edit existing colors
in the patch as well if you want to.

7. Repeat this process for each pat file the car has, the menu pat and the lod/open pat.
Also, menu pats and lod/open pats have different data sizes, so you can't use the same PNG strip for
both. You will want to take note of the exact hue shift settings / effects you applied to the first one,
then apply the same exact settings to the other, to get consistent results between the menu model and lod/open model.

8. Last, overwrite the new menu pat file into the menu model.
Highlight the entire data chunk, then paste the new pat file over it.
Make sure that it overwrites the old data, then inserts the overflow, so that
no data beyond the pat is erased.

After that, update the menu model offsets that are affected.
(See image)

Now simply oveerwrite the original lod/open pat with the new one.

To register the new paint color into the game, update the spec database's VARIATION[region] table
and add a new entry for the car, making sure to at least update the VarOrder cell, but also
the swatch color settings.
