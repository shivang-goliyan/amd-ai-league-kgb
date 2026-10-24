# Match 4 — web retrieval preparation

The public event page lists Intelligent Web Information Retrieval as live through October 27. Its detailed-brief link currently leads back to the event page, and the existing submission form exposes only the Match 2 and 3 image fields. The official Match 4 interface and submission route are still needed.

Implemented so far: a structure-aware page reader, tested on synthetic HTML fixtures. It preserves table row relationships and JSON-LD values, excludes hidden decoy elements and executable script contents, resolves ordinary and HTML-base-relative links, excludes non-HTTP navigation targets, and retains phone/email values contained in link attributes. These are page-processing tests, not end-to-end agent accuracy results.

Next: connect bounded navigation and the resident AMD model to the official input/output contract, validate against permitted examples and independent held-out cases, measure GPU latency/VRAM, and submit through the official route. No Match 4 completion or score is claimed.
