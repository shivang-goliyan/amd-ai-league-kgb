FROM rocm/pytorch:rocm10.0_ubuntu26.04_py3.14_pytorch_release_2.13.0
WORKDIR /app
ENV PYTHONUNBUFFERED=1 TOKENIZERS_PARALLELISM=false HF_HUB_DISABLE_TELEMETRY=1 \
    OCR_MODEL_DIR=/models/ocr OCR_SOCKET=/tmp/league-ocr.sock
COPY app/requirements.txt /app/requirements.txt
# Resolve and lock dependencies outside the image, then install exactly that list.
# Never let pip replace the ROCm torch with a CUDA build.
RUN python3 -c "import torch; assert torch.version.hip; print(torch.__version__)" \
    && python3 -m pip install --no-cache-dir --no-deps -r /app/requirements.txt \
    && python3 -c "import torch; from transformers import AutoProcessor, Qwen3VLForConditionalGeneration; assert torch.version.hip; print(torch.__version__)"
ARG MODEL_REVISION=0c351dd01ed87e9c1b53cbc748cba10e6187ff3b
RUN python3 -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen3-VL-8B-Instruct', revision='${MODEL_REVISION}', local_dir='/models/ocr', allow_patterns=['*.json','*.safetensors','*.txt','*.jinja','*.model','LICENSE*','NOTICE*'])"
COPY app/ /app/
RUN mkdir -p /app/input /app/output \
    && python3 -m compileall -q /app \
    && python3 -c "from pathlib import Path; assert Path('/models/ocr/model.safetensors.index.json').is_file()"
ENV HF_HUB_OFFLINE=1 TRANSFORMERS_OFFLINE=1
HEALTHCHECK --interval=3s --timeout=2s --start-period=9m --retries=3 CMD python3 -c "import pathlib; assert pathlib.Path('/tmp/league-ocr.sock').is_socket()"
CMD ["python3", "/app/start.py"]
