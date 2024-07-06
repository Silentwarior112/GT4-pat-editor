# GT4-pat-editor
Basic python scripts that modify the color patch files in Gran Turismo 4, which allow for custom colors on certain cars.

Current tooling is crude and unfinished, and requies using multiple separate scripts

Credit goes to Nenkai for file format research and figuring.
https://github.com/Nenkai/GT-File-Specifications-Documentation

To do:
- Integrate all scripts into one

Bringing back the Pink Vitz:
<p align="center">
  <img width="640" height="360" src="https://github.com/Silentwarior112/GT4-pat-editor/blob/main/pink%20vitz.PNG">
</p>

Adding the infamous Y49 Barbados Yellow to the 1990 CR-X:
<p align="center">
  <img width="640" height="360" src="https://github.com/Silentwarior112/GT4-pat-editor/blob/main/yellowcrx.png">
</p>

How to use:

1. Extract the .pat file from the Menu model and save to a separate file.
Before starting, it's recommended to copy the menu model and the lod/open pat file
to a separate folder to keep things organized.

Using the model extractor & rebuilder script, click "Extract model" and find your model file.
Then, select the desired assets to extract from the model.
For this, you would only need to select the MainModelColorPatch, and maybe the WheelColorPatch if
that particular car has multiple wheel colors and you want to add extra wheel colors.
Examples of these are: 'integra_r_03' (hond0036) and '_5_turbo_80' (re__0003).
Save the files, then proceed to modify the color patch file.

2. Using the color adder script, add additional color entries to the pat file and save.
Do this for both the menu pat, and the lod/open pat.

3. Next, open the color editor script. Select one of the paint tabs, and export
it to a PNG. You will want to also export a different paint as well, so that you
can compare the difference between them, so that you will know which pixels to modify.
When choosing which color to use for determining which pixels are the right ones,
it's best to compare two colors that are not shades.
For example, green and blue.

4. Open the PNGs in an image editor, and splice the strips together.
Pick one of strips to modify.
Use the color picker tool to check the difference between the pixels
on each strip. Looking at the V in the HSV will make it obvious
if a pixel is different (thus a relevant pixel) versus the same (not relevant).
Take the selection tool on add mode, and
select each relevant pixel in the strip.
Alternate between the color picker and selection tool until all relevant pixels are selected.
Once they are all selected, apply your desired adjustments/effects.
Really though, the only practical adjustment is the Hue.
The best way to modify the hue is to use the levels tool (paint.net)
or equivalent. Find the brightest, most opaque, and most saturated pixel in the strip,
and use the color values from it as the input values in the levels tool.
Then, set the output values in the levels tool to a desired color.
For example, you can look up a manufacturer paint code and
convert it to an approximated RGB value to use here.
Other effects and adjustments to the pixels will likely
mess up the shading, so be mindful.
The most obvious sign of poor editing is the door handle area of the car.
Once the strip is modified, get rid of the comparison strip and
then save the new png.
Before closing the image editor, it would also be wise to
separately save a 'selection layer' that marks every pixel that needs to be edited.

5. Go back to the color editor, and import your PNG strip into whichever paint tab you want to overwrite, then save.
This should be the new one that you added in the previous step, but you can also edit existing colors
in the patch as well if you want to.

6. Repeat this process for each pat file the car has, the menu pat(s) and the lod/open pat(s).
Also, menu pats and lod/open pats have different data sizes, so you can't use the same PNG strip for
both. You will want to take note of the exact hue shift settings / effects you applied to the first one,
then apply the same exact settings to the other, to get consistent results between the menu model and lod/open model.

7. Update the menu model with the new pat file(s).
Go back to the the model extractor & rebuilder script to overwrite the new menu pat file(s) into the menu model.

8. With your new Menu model and new lod/open patch file, simply overwrite the original file(s) with the new ones.

To register the new paint color into the game, update the spec database's VARIATION[region] table
and add a new entry for the car, making sure to at least update the VarOrder cell, but also
the swatch color settings. 
To set the swatch color, take your RGB values and convert them to hexadacimal.

For example: 248,185,21 = F8B915
The format of the swatch setting: Unknown value (1 digit), blue, green, red
For this paint code, we can use 5 | 15 | B9 | F8, or 515B9F8.
Convert that back into a decimal value and input it into the spec database.
515B9F8 = 85309944

