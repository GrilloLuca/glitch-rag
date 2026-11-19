# Azure migration plan (draft, 2026-11-18)

Goal: run the same service on Azure, with managed models, managed search and no secrets
in configuration, and prove with the existing evaluation that quality did not regress.

Scheduled for week 4, after a local container step at the end of week 3 (step 0). The
Azure free credit lasts 30 days from activation: activate it on the first day of week 4,
when an image is ready to deploy, and set a budget alert immediately.

## Step 0: containers on the laptop (end of week 3)

Everything that does not need Azure is built and tested locally first, at no cost.

- **`Dockerfile`** for the API: dependencies installed with `uv` from `uv.lock`, a small
  runtime image, no secrets or `data/` inside it, configuration only through environment
  variables. The same image is deployed to Container Apps in week 4.
- **`docker-compose.yml`** with the API and **Qdrant** as a local vector database, with
  its storage in a volume under `data/` (never committed).
- **Ollama stays native on the Mac.** The container reaches it at
  `http://host.docker.internal:11434/v1`. On macOS containers run in a VM with limited
  memory, and the 7B model needs about 5–6 GB.
- **Search `Protocol`** (next section) with two implementations, numpy and Qdrant, chosen
  by a `SEARCH_BACKEND` setting. Indexing writes to Qdrant from the same embeddings.
- **Optional: Azurite**, the official Blob Storage emulator, to develop indexing from Blob
  before creating the real storage account. Azure AI Search has no local emulator.
- **Gate**: `eval_rag` with numpy and with Qdrant on the same questions. Same embeddings
  and exact search should give the same retrieval numbers; any difference is a bug or an
  approximation of the index (HNSW) to explain. Then compare Qdrant's hybrid search with
  the local BM25 + RRF.

At the end of week 4 the same questions run against three search implementations:
numpy, Qdrant and Azure AI Search.

## From local to Azure

| Today (local) | On Azure | Code change |
|---|---|---|
| `qwen2.5:7b` on Ollama | A chat model deployed in Microsoft Foundry | Small: `LLM_BASE_URL`, `LLM_MODEL`, authentication |
| `bge-m3` on Ollama | An embedding model deployed in Foundry | Small in code, but **every index must be rebuilt**: vectors from different models are not comparable |
| numpy + BM25 + RRF in memory | Azure AI Search: vector, keyword and hybrid queries, semantic ranker, filters | Large: a new search implementation and indexing that writes to AI Search |
| `data/` on disk | Blob Storage for raw exports; AI Search holds the index | Indexing scripts read from Blob |
| `.env` with an API key | Container Apps settings, Key Vault for secrets, Managed Identity instead of keys | The client accepts an Entra ID token as well as a key |
| `fastapi dev` on a laptop | Azure Container Apps, from a `Dockerfile` | New `Dockerfile`; app code unchanged |
| Terminal logs | Application Insights via OpenTelemetry | Logging and tracing setup |
| Tests run by hand | GitHub Actions: lint, tests, image build and deploy | New workflow file |

## The search interface comes first

`answer_question` receives a `ReviewSearch` and works with **positions** in a list
(`search.reviews[i]`). Azure AI Search returns documents, not positions. Before touching
Azure:

1. Define a `Protocol` for search that returns documents (id, text, metadata, score),
   with `semantic`, `keyword` and `hybrid` methods.
2. Make the current numpy/BM25 code its first implementation; `rag.py` depends only on
   the protocol.
3. Add Qdrant (step 0) and then AI Search behind the same protocol, selected by
   configuration.

Local development and tests keep working, and the two implementations can be compared on
the same questions.

## Evaluation is the gate

The week 2 baseline (`docs/rag.md`, Run 3) is the reference. After each step, run:

```bash
uv run python -m scripts.eval_rag evals/rag_questions.jsonl azure-<step>
```

and compare doc hit@3, cited expected doc, correct declines, expected facts, invented
citations and latency. Change one component at a time:

1. Foundry chat model, local search and local embeddings: measures the model alone.
2. Foundry embeddings, local numpy search, indexes rebuilt: measures the embedding model.
3. AI Search with the same embeddings: measures the search engine.
4. AI Search hybrid and semantic ranker: measures the features we could not build locally.

Hybrid search lost to semantic search locally (83% vs 94% precision@5). AI Search's
hybrid with the semantic ranker is a different system and must be measured, not assumed.

## Limits and costs to check

- **AI Search Free tier**: 50 MB of total storage and 3 indexes per service. The review
  vectors alone are about 48 MB (11,692 × 1024 float32), so the full review index does
  not fit. Options:
  - index only recent reviews (e.g. from 2023);
  - use a smaller embedding dimension or compressed vectors (float16, int8, scalar
    quantization);
  - use the Serverless Developer tier (preview, billed per GB, not for production) or
    Basic (fixed monthly cost: check the pricing page against the credit).
  The documentation index (44 chunks) fits in any tier.
- **Model quota and region**: check which chat and embedding models are deployable in
  the chosen region before creating resources.
- **Latency**: 53 s per question locally on CPU; record the Azure number per step.
- **Cold start**: the first local question took 118 s (model loading). Container Apps
  scaled to zero has its own cold start: decide between min replicas 0 (cheaper) and 1.

## Open decisions

- Chat model on Foundry: a small model close to the local one, or a stronger one? A
  stronger model may fix omissions and merged complaints, but then the comparison
  measures two things at once. Proposal: step 1 with a small model, then one run with a
  stronger model as a separate experiment.
- Embedding model and dimension (affects storage, cost and the Free tier).
- Which reviews to index on Azure (all, or a time window).
- Region, resource naming and one resource group for everything, so the whole
  environment can be deleted in one step.
- Infrastructure as code (Bicep or `azd`) from the start, or the portal first and code
  afterwards.

## Outline

End of week 3 (step 0, no Azure):

1. Search protocol refactor, local only, tests green, evaluation unchanged.
2. `Dockerfile`, `docker compose` with Qdrant, Qdrant search implementation, evaluation.

Week 4:

1. Activate the credit, budget alert, resource group, Foundry project, model deployments.
2. Step 1 and 2 of the evaluation from the laptop (Foundry chat, then Foundry
   embeddings).
3. Push the step 0 image to a container registry and run it on Container Apps with the
   Foundry models: in the cloud it cannot reach Ollama on the laptop.
4. AI Search index, indexing script, step 3 and 4 of the evaluation.
5. Managed Identity and Key Vault: remove every key from the configuration.
6. Application Insights, GitHub Actions, README update.
