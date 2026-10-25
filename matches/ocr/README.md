# Match 2: resident vision-language OCR

Native Radeon GPU evaluation passed 10 public illustrations and 32 synthetic stress cases. Submission and mandatory-container/Instinct validation remain pending; see [validation details](../../VALIDATION.md).

Uses the Apache-2.0 Qwen3-VL-8B-Instruct model, pinned to a specific model revision. The model remains in a single ROCm process while fresh grader calls use a lightweight Unix-socket client. No third-party inference API is called. The required ROCm base layers are retained and model weights are downloaded during the image build.

The grader calls:

```sh
python3 /app/app.py --input-image /app/input/image_01.png
```

The client atomically writes `/app/output/image_01_output.json` with the recognized text. PNG, JPEG and TIFF decoding, EXIF orientation, transparency and 16-bit integer TIFF normalization are supported. Images are resized with their aspect ratio preserved and centered on a white 1024-square canvas. The startup warmup uses the same shape, avoiding first-use GPU delays for each source aspect ratio.

The transcription prompt preserves Chinese province prefixes, omits banners surrounding US plate registrations, joins sign lines in reading order, and does not add units. Deterministic cleanup removes formatting wrappers; it never substitutes an identifier based on a sample answer.

## Verification

```sh
python3 -m unittest discover -s tests -v
```

These CPU tests verify decoding, output files, failure handling and actual socket transport between independent client processes. They do not measure OCR accuracy or GPU latency. GPU validation must additionally cover the ten official illustrative examples, independent degraded images, startup duration, per-request latency, peak VRAM and the mandated base layers / 60 GiB uncompressed size limit.

Container references belong only in the private submission field and are not committed here.
