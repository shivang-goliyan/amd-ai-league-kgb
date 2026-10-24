"""Create deterministic synthetic OCR tests, separate from the official samples.

No generated image or expected answer is included in the inference container.
"""
import argparse
import json
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageEnhance,ImageFilter


def main():
    p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);args=p.parse_args();args.output.mkdir(parents=True,exist_ok=True)
    english=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',64)
    cjk=ImageFont.truetype('/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc',64)
    small=ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf',24)
    examples=[('plate_a','8KLR204','plate'),('plate_b','2VHZ691','plate'),('plate_cn','粤C·59027','chinese'),('sign_a','BRIDGE\nCLOSED','sign'),('sign_b','SPEED LIMIT\n45','sign'),('sign_c','LANE ENDS\nMERGE LEFT','sign'),('sign_d','YIELD','sign'),('sign_e','40','sign')]
    records=[]
    for name,text,kind in examples:
        color=(225,235,255) if kind=='chinese' else 'white';image=Image.new('RGB',(900,420),color);draw=ImageDraw.Draw(image);draw.rounded_rectangle((20,20,880,400),radius=20,outline='black',width=7)
        if kind=='plate':draw.text((450,65),'CALIFORNIA',font=small,fill='black',anchor='mm')
        draw.multiline_text((450,220),text,font=cjk if kind=='chinese' else english,fill='black',anchor='mm',align='center',spacing=20)
        variants=[('clean',image),('blur',image.filter(ImageFilter.GaussianBlur(1.6))),('dark',ImageEnhance.Brightness(image).enhance(.32)),('angle',image.rotate(8,resample=Image.Resampling.BICUBIC,expand=True,fillcolor='white'))]
        for i,(variant,picture) in enumerate(variants):
            fmt=['PNG','JPEG','TIFF','PNG'][i];ext={'PNG':'png','JPEG':'jpg','TIFF':'tiff'}[fmt];file=f'{name}_{variant}.{ext}';picture.save(args.output/file,format=fmt)
            records.append({'file':file,'text':' '.join(text.split()),'source':'synthetic held-out; clean, blur, low-light, and rotation variants'})
    (args.output/'expected.json').write_text(json.dumps(records,ensure_ascii=False,indent=2)+'\n');print('Created',len(records),'synthetic stress cases; no inference results yet.')

if __name__=='__main__':main()
