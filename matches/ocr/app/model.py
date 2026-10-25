"""Qwen3-VL transcription on an AMD GPU. No remote inference endpoints."""
import os
from contract import clean_text, load_image, prepare_for_ocr

PROMPT='''Transcribe the text in this image. Return ONLY the requested visible text, without explanations, JSON, labels, or quotation marks.
If it is a vehicle license plate, return the registration number only. Omit jurisdiction banners and decorative slogans printed around the number. A Chinese province character and its following letter ARE part of the registration and must be kept.
If it is a road sign, keep every printed word and number, reading lines top to bottom and joining them with spaces. If only digits are printed, return only those digits; do not add units or implied words.
Preserve the visible characters. Do not guess replacements for ambiguous letters or numbers. If no text is readable, return an empty string.'''

class Recognizer:
    def __init__(self):
        import torch
        from transformers import AutoProcessor, Qwen3VLForConditionalGeneration
        if not torch.version.hip or not torch.cuda.is_available():
            raise RuntimeError('A working ROCm PyTorch GPU is required; CPU fallback is disabled')
        self.torch=torch
        location=os.getenv('OCR_MODEL_DIR','/models/ocr')
        self.processor=AutoProcessor.from_pretrained(location,local_files_only=True,min_pixels=256*32*32,max_pixels=1024*1024)
        self.model=Qwen3VLForConditionalGeneration.from_pretrained(location,local_files_only=True,dtype=torch.bfloat16,attn_implementation='sdpa').to('cuda').eval()
        torch.manual_seed(0)
        print('Loaded OCR model on',torch.cuda.get_device_name(0),'HIP',torch.version.hip,flush=True)

    def __call__(self,path):
        image=load_image(path)
        return self.transcribe(image)

    def transcribe(self,image):
        image=prepare_for_ocr(image)
        messages=[{'role':'user','content':[{'type':'image','image':image},{'type':'text','text':PROMPT}]}]
        inputs=self.processor.apply_chat_template(messages,tokenize=True,add_generation_prompt=True,return_dict=True,return_tensors='pt').to('cuda')
        inputs.pop('token_type_ids',None)
        with self.torch.inference_mode():
            generated=self.model.generate(**inputs,max_new_tokens=96,max_time=20.0,do_sample=False,use_cache=True)
        text=self.processor.batch_decode(generated[:,inputs['input_ids'].shape[-1]:],skip_special_tokens=True,clean_up_tokenization_spaces=False)[0]
        return {'text':clean_text(text)}
