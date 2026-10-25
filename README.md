# AMD AI League — KGB

Solo project for the 2026 AMD AI League. [Matches 2 and 3 submitted for grading](https://lablab.ai/ai-hackathons/amd-lablab-ai-academy-challenge/kgb/kgb-grounded-ocr-and-rag-on-amd).

- **Match 2:** resident Qwen3-VL OCR process on AMD ROCm; lightweight grader client with atomic output JSON.
- **Match 3:** defensive multi-format document retrieval, evidence checks and resident model/client architecture.
- **Match 4:** seeded HTTP navigation and resident model prototype; awaiting the official detailed brief and submission contract.

CPU behavioral tests and preliminary native Radeon GPU evaluations pass. OCR passed ten public illustrations and 32 synthetic stress cases; RAG passed ten public sample questions; the web prototype passed nine owned HTTP fixture tasks. [Validation details](VALIDATION.md) distinguish these results from mandatory-container/Instinct verification and private grading. No competition score or prize is claimed.

The model is open-source and runs locally on AMD hardware; there are no hosted inference APIs. Registry references are kept out of this source repository and supplied only to the private submission form.

```sh
python3 -m unittest discover -s matches/ocr/tests -v
```

See each match directory for its invocation contract and validation limits.

Build publishing uses Docker Hub. The mandated base contains a roughly 20 GB compressed layer; GitHub Container Registry has a 10 GB per-layer limit. The required AMD layers are preserved rather than flattened.
