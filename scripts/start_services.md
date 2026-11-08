# Local services

Three long-running processes, each in its own terminal, plus Postgres in Docker.
Tested on an Apple Silicon Mac (Metal). Install llama.cpp with `brew install llama.cpp`.

## 1. Embeddings: jina-embeddings-v4 (port 8081)

```bash
llama-server -hf jinaai/jina-embeddings-v4-text-retrieval-GGUF:Q8_0 \
  --embedding --pooling mean --no-mmproj \
  -c 32768 --parallel 4 -b 8192 -ub 8192 --port 8081
```

- `--pooling mean` is required for this model.
- `--no-mmproj` skips the image encoder; text only.
- `-b/-ub 8192` and 8,192 tokens per slot: some BIRD schema chunks exceed 2,048 tokens.
- If Metal reports `Insufficient Memory`, use `-c 16384 --parallel 2` and make sure no other model (e.g. Ollama) is loaded.

## 2. Reranker: bge-reranker-v2-m3 (port 8082)

```bash
llama-server -hf gpustack/bge-reranker-v2-m3-GGUF:Q8_0 --reranking -c 8192 --port 8082
```

## 3. LLM gateway: LiteLLM (port 4000)

```bash
export ANTHROPIC_API_KEY=...        # from console.anthropic.com
export LITELLM_MASTER_KEY=sk-...    # any strong value; required by LiteLLM
uvx --from 'litellm[proxy]' litellm --config config/litellm.yaml --port 4000
```

## 4. Postgres catalog

From the auto-ontology checkout (fresh catalog before every build):

```bash
docker compose down -v && docker compose up -d postgres
```

## Smoke tests

```bash
# Embeddings: expect "2 2048"
curl -s localhost:8081/v1/embeddings -H 'Content-Type: application/json' \
  -d '{"model":"jina-embeddings-v4","input":["customer table","order date"],"encoding_format":"float","input_type":"passage","truncate":"END","modality":"text"}' \
  | python3 -c "import sys,json; d=json.load(sys.stdin)['data']; print(len(d), len(d[0]['embedding']))"

# Reranker: expect relevance_score per document
curl -s localhost:8082/v1/rerank -H 'Content-Type: application/json' \
  -d '{"model":"bge-reranker-v2-m3","query":"which team a player belongs to","documents":["match results","player team membership","weather"],"top_n":3}'

# Gateway: expect "OK"
curl -s localhost:4000/v1/chat/completions -H 'Content-Type: application/json' \
  -H "Authorization: Bearer $LITELLM_MASTER_KEY" \
  -d '{"model":"azure/anthropic/claude-haiku-5-5","messages":[{"role":"user","content":"Say OK"}]}'
```
