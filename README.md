# AMD AI League — KGB

Solo work in progress for the 2026 AMD AI League.

- **Match 2:** resident Qwen3-VL OCR process on AMD ROCm; lightweight grader client with atomic output JSON.
- **Match 3:** planned defensive multi-format document retrieval with exact evidence citations.
- **Match 4:** awaiting the official detailed brief and submission contract.

The OCR decoding/output/IPC tests pass locally. Recognition accuracy, latency, VRAM and the complete ROCm image still require verification on the authorized hackathon GPU pool. No competition score or prize is claimed.

The model is open-source and runs locally on AMD hardware; there are no hosted inference APIs. Registry references are kept out of this source repository and supplied only to the private submission form.

```sh
python3 -m unittest discover -s matches/ocr/tests -v
```

See each match directory for its invocation contract and validation limits.
