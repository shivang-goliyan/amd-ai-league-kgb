# Match 2: resident vision-language OCR

Work in progress. Not yet submitted or validated on the hackathon AMD GPU pool.

Uses the Apache-2.0 Qwen3-VL-8B-Instruct model, pinned to a specific model revision. The model remains in a single ROCm process while fresh grader calls use a lightweight Unix-socket client. No third-party inference API is called. The required ROCm base layers are retained and model weights are downloaded during the image build.

The grader calls:

```sh
python3 /app/app.py --input-image /app/input/image_01.png
```

The client atomically writes `/app/output/image_01_output.json` with the recognized text. PNG, JPEG and TIFF decoding, EXIF orientation, transparency and 16-bit integer TIFF normalization are supported. Input image edges are bounded before inference.

The transcription prompt preserves Chinese province prefixes, omits banners surrounding US plate registrations, joins sign lines in reading order, and does not add units. Deterministic cleanup removes formatting wrappers; it never substitutes an identifier based on a sample answer.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

These CPU tests verify decoding, output files, failure handling and actual socket transport between independent client processes. They do not measure OCR accuracy or GPU latency. GPU validation must additionally cover the ten official illustrative examples, independent degraded images, startup duration, per-request latency, peak VRAM and the mandated base layers / 60 GiB uncompressed size limit.

Container references belong only in the private submission field and are not committed here.
