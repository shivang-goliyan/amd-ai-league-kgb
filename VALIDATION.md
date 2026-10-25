# Validation evidence

These are development measurements, not private grader results or League points. Native evaluation used an AMD Radeon gfx1100 GPU, ROCm 7.2, PyTorch 2.11, Transformers 5.15 and Python 3.12. The mandated containers use ROCm 10 / PyTorch 2.13 / Python 3.14. Native results do not establish container or Instinct parity.

| Component | Evaluation | Result |
| --- | --- | --- |
| OCR, source `9a3cba1` | Ten official PDF illustrations re-encoded in the stated PNG/JPEG/TIFF formats | 10/10; slowest 1.76 seconds |
| OCR, source `9a3cba1` | 32 independently generated plate/sign cases with blur, darkness and rotation | 32/32; slowest 1.77 seconds |
| RAG, source `a97575c` | Ten official public sample questions, checking answer aliases and exact necessary citation sets | 10/10; slowest query 8.87 seconds; indexing 31.66 seconds |
| Web prototype, source `d1ef66b` | Six owned HTTP fixture tasks with genuine local GPU decisions: navigation, table values, structured price, late-page evidence, refusal and redirects | 6/6; slowest 6.77 seconds; unofficial prototype only |

A device-wide VRAM sampler ran every three seconds and observed a 17.84 GiB peak in the archived measurement window. The model performs real GPU inference; no dummy memory buffers or CPU inference fallback are used. The standalone OCR service became ready in 20 seconds on a host already used for preceding experiments; this is not a fresh-host startup guarantee.

The initial OCR implementation had first-use timing failures (8/10 public illustrations and 30/32 stress cases); a warm public repeat passed 10/10. It was changed to preserve aspect ratio inside a fixed 1024-square canvas and warm that same GPU shape at startup. The final results above run the actual updated program against original fixture formats, without offline pre-padding the test inputs.

The first RAG run passed 9/10 because an interrupted image transcription was stored as partial text. The revised implementation requires an end token, retries once within a shared indexing budget, and skips an image if transcription remains incomplete. A real GPU fault-injection check forced a one-token output and confirmed recovery through a second complete transcription. The sample question run followed that recovery check, so it is not an untouched cold-host measurement.

There are 77 passing CPU behavioral tests: OCR 14, RAG 33, web 27 and base identity checks 3. These verify transport, parsing, evidence checks and control flow; they do not measure model accuracy.

The revised RAG container build passed on [GitHub Actions](https://github.com/shivang-goliyan/amd-ai-league-kgb/actions/runs/40142247405). Its anonymous manifest/config checks confirmed all 11 original AMD base layers, and CI enforced the 60 GiB uncompressed limit and ROCm import. The [revised OCR build](https://github.com/shivang-goliyan/amd-ai-league-kgb/actions/runs/40159020018) also passed, including the packaged tokenizer and vision processor with network access disabled. Both revised images resolve anonymously and preserve all 11 required base layers.

A separate web multi-hop check initially returned the correct value but omitted the page mapping the named incident to its defect identifier. Revised evidence instructions are undergoing GPU revalidation; the six-case baseline above is not a claim that this citation gap is resolved.

No private evaluation score, prize or new League points is claimed here. Match 4 still lacks an official detailed specification and submission field; the seeded HTTP prototype does not claim compliance with an invented grader contract. JavaScript rendering and an independent search backend remain unimplemented.
