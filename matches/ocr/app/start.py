"""Load once, warm up, then keep the container available for grader exec calls."""
import os
import signal
from PIL import Image
from model import Recognizer
from service import make_server

if __name__=='__main__':
    recognize=Recognizer()
    recognize.transcribe(Image.new('RGB',(256,256),'white'))
    server=make_server(os.getenv('OCR_SOCKET','/tmp/league-ocr.sock'),recognize)
    print('OCR_READY',flush=True)
    try:server.serve_forever(poll_interval=.2)
    finally:server.server_close()
