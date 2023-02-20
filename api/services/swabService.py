
from io import BytesIO
import base64
from PIL import Image, ImageFont, ImageDraw
import textwrap
from common.util import encode128

def serve_pil_image(specimen_id, fname, lname, dob, organization_name, col_date, col_time, type):
    
    img = Image.new('RGBA', (2100, 700))

    lname = lname.upper()
    fname = fname.title()

    # textwrap.wrap(text, width=70
    # lname = lname.replace(' ', '\n') 
    # fname = fname.replace(' ', '\n') 

    if type==1: # vial wrapper
        character_limit = 17
        bc_fnt = ImageFont.truetype('/home/static/fonts/code128.ttf', 250) #LibreBarcode128Text-Regular.ttf code128.ttf
        fnt = ImageFont.truetype('/home/static/fonts/ArialNarrow.ttf', 80)
        fnt_lg = ImageFont.truetype('/home/static/fonts/ArialNarrow.ttf', 130)

        offset_col2 = 1420

        line_1a = 40
        line_2a = 375
        line_3a = 500

        line_1b = 440
        
        line_2b = 540
    else:
        character_limit = 22

        bc_fnt = ImageFont.truetype('/home/static/fonts/code128.ttf', 400) #LibreBarcode128Text-Regular.ttf code128.ttf
        fnt = ImageFont.truetype('/home/static/fonts/ArialNarrow.ttf', 100)
        fnt_lg = ImageFont.truetype('/home/static/fonts/ArialNarrow.ttf', 200)

        offset_col2 = 1020

        line_1a = 0
        line_2a = 400
        line_3a = 480

        line_1b = 455
        
        line_2b = 555

    lname = textwrap.fill(lname, width=character_limit)
    fname = textwrap.fill(fname, width=character_limit)

    d = ImageDraw.Draw(img)

    d.text((-34,line_1a), encode128(specimen_id), font=bc_fnt, fill=(0, 0, 0))
    d.text((0, line_2a), organization_name, font=fnt, fill=(0, 0, 0))
    d.text((0, line_3a), specimen_id, font=fnt_lg, fill=(0, 0, 0))
    
    d.text((offset_col2, line_1a), '{},\n{}'.format(lname, fname), font=fnt, fill=(0, 0, 0))
    d.text((offset_col2, line_1b), 'DOB: {}'.format(dob), font=fnt, fill=(0, 0, 0))
    d.text((offset_col2, line_2b), '{} {}'.format(col_date, col_time), font=fnt, fill=(0, 0, 0))


    img_io = BytesIO()
    img=img.rotate(90, expand=1) # degrees counter-clockwise
    img.save(img_io, 'PNG')
    img_io.seek(0)
    
    return u"data:image/png;base64," + base64.b64encode(img_io.getvalue()).decode("ascii")
