"""Image decoding and exact file contract for AMD AI League Match 2."""
import json
import math
import os
import re
import tempfile
from pathlib import Path
from PIL import Image, ImageOps


def clean_text(value):
    value=str(value).strip()
    value=re.sub(r'^```(?:text|plaintext)?\s*\n?', '', value, flags=re.I)
    value=re.sub(r'\s*```$', '', value)
    value=re.sub(r'^(?:text|transcription|recognized(?: text)?|answer)\s*:\s*','',value,flags=re.I)
    value=value.strip().strip('"\'“”')
    return ' '.join(value.split())


def load_image(path, max_edge=1600):
    with Image.open(path) as source:
        image=ImageOps.exif_transpose(source).copy()
    if image.mode.startswith('I;16') or image.mode=='I':
        image=image.convert('I').point(lambda x: x*(255/65535)).convert('L')
    if image.mode in ('RGBA','LA') or 'transparency' in image.info:
        rgba=image.convert('RGBA');canvas=Image.new('RGBA',rgba.size,'white');canvas.alpha_composite(rgba);image=canvas.convert('RGB')
    else:
        image=image.convert('RGB')
    image.thumbnail((max_edge,max_edge),Image.Resampling.LANCZOS)
    return image


def write_answer(input_image, answer, output_dir=Path('/app/output')):
    output_dir=Path(output_dir);output_dir.mkdir(parents=True,exist_ok=True)
    result={'text':clean_text(answer.get('text',''))}
    confidence=float(answer.get('confidence',0))
    result['confidence']=max(0,min(1,confidence)) if math.isfinite(confidence) else 0.0
    target=output_dir/(Path(input_image).stem+'_output.json')
    fd,tmp=tempfile.mkstemp(prefix='.',suffix='.tmp',dir=output_dir)
    try:
        with os.fdopen(fd,'w',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False);f.write('\n')
        os.replace(tmp,target)
    finally:
        if os.path.exists(tmp):os.unlink(tmp)
    return target
