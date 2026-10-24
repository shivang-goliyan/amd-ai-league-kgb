FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0
WORKDIR /app
ENV PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_TELEMETRY=1 \
    OCR_MODEL_DIR=/models/ocr RAG_SOCKET=/tmp/league-rag.sock
COPY matches/rag/app/requirements.txt /app/requirements.txt
RUN python3 -c "import torch; assert torch.version.hip" \
    && python3 -m pip install --no-cache-dir --no-deps -r /app/requirements.txt \
    && python3 -c "import torch; from transformers import Qwen3VLForConditionalGeneration; assert torch.version.hip"
ARG MODEL_REVISION=0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
RUN python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-VL-8B-Instruct', revision='${MODEL_REVISION}', local_dir='/models/ocr', allow_patterns=['*.json','*.safetensors','*.txt','*.jinja','*.model','LICENSE*','NOTICE*'])"
COPY matches/ocr/app/model.py /app/vision.py
COPY matches/ocr/app/contract.py /app/contract.py
COPY matches/rag/app/ /app/
RUN mkdir -p /app/corpus /app/output /app/index && python3 -m compileall -q /app
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
HEALTHCHECK --interval=3s --timeout=2s --start-period=9m --retries=3 CMD python3 -c "import pathlib; assert pathlib.Path('/tmp/league-rag.sock').is_socket()"
CMD ["python3", "/app/start.py"]
