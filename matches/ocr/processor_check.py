"""Check the packaged tokenizer/vision processor offline, without GPU inference."""
from PIL import Image
from transformers import AutoProcessor
from contract import prepare_for_ocr
from model import PROMPT


processor=AutoProcessor.from_pretrained('/models/ocr',local_files_only=True,min_pixels=256*32*32,max_pixels=1024*1024)
image=prepare_for_ocr(Image.new('RGB',(1500,300),'white'))
inputs=processor.apply_chat_template(
    [{'role':'user','content':[{'type':'image','image':image},{'type':'text','text':PROMPT}]}],
    tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt')
assert inputs['input_ids'].ndim==2 and inputs['input_ids'].shape[0]==1
assert inputs['pixel_values'].numel()>0
assert inputs['image_grid_thw'].shape==(1,3)
print('Offline tokenizer/vision processor passed:',{k:tuple(v.shape) for k,v in inputs.items()})
