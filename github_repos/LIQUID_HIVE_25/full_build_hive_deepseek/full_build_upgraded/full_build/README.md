# As-Smart-As-Possible AI Agent Build

This build provides a scalable foundation for a self‑improving question answering agent built from "small" language models (≤8 B parameters).  It implements a **dual‑index retrieval system**, a **self‑loop controller** with verifiers, a **domain router**, an evaluation harness and a simple memory/cache layer.  Each component is cleanly separated so you can swap in your own models, datasets or storage back‑ends.

## Features

- **Dual‑Index RAG** – combines a dense embedding index with a sparse BM25 index.  At query time the two scores are cross‑scored to return a ranked list of documents and associated citations.
- **Self‑Loop Controller** – runs iterative cycles of plan → draft → critic → verify → revise until a confidence threshold is met.  Integrates external verifiers for code and math, and includes a one‑shot debate mode with a judge.
- **Verifiers** – syntax and static analysis for code blocks, symbolic checking for math expressions, and citation/consistency checks for retrieved facts.
- **Router and Model Ensemble** – selects a path (CODE, MATH, RAG, GENERAL) and the appropriate model size based on the query.  Supports pluggable domain LoRA adapters.
- **Evaluation Harness** – allows you to run regression tests and compute metrics such as exact match, F1, pass@1 and citation precision.
- **Memory and Cache** – simple long‑term store with pruning and a key–value cache for plans and answers.  Prunes low‑entropy or old items on a schedule.
- **Ops/Security Stubs** – scaffolds for authentication, quotas, logging and metrics collection.

## Getting Started

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
2.  Populate `data/corpus/` with your domain documents.  See `retrieval/dual_index.py` for the expected schema.
3.  Train or load your dense embedding model and update `retrieval_config.yaml` accordingly.
4.  Run the retrieval indexer:
    ```bash
    python -m retrieval.dual_index --build
    ```
5.  Integrate your LLM client by subclassing `SelfLoop.ChatClient` and implementing `generate()`; then call `self_loop()` from `self_loop.py`.

See each module for further instructions and stub methods you need to hook into.

## Layout

```
full_build/
├── README.md              # this file
├── config/                # YAML/JSON configuration files
├── evaluation/            # harness and metrics
├── memory_cache/          # simple memory and caching utilities
├── ops_security/          # ops/security scaffolding
├── retrieval/             # dual‑index RAG and utilities
├── router/                # query router and cost gating
├── self_loop.py           # core self‑loop controller
└── verifiers/             # code/math/retrieval verifiers
```

Each Python module is extensively documented and designed for extension.