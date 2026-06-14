#!/usr/bin/env bash
# 2단계 순화 LLM: LoRA 병합 → GGUF 변환(Q6_K) → Ollama 등록
# 역할 분담: 사용자가 학습 머신에서 실행. llama.cpp 가 필요하다.
set -euo pipefail

BASE="${BASE:-Qwen/Qwen2.5-14B-Instruct}"
ADAPTER="${ADAPTER:-outputs/qwen-sunhwa-lora}"
MERGED="${MERGED:-outputs/qwen-sunhwa-merged}"
LLAMACPP="${LLAMACPP:-$HOME/llama.cpp}"   # git clone https://github.com/ggerganov/llama.cpp
QUANT="${QUANT:-Q6_K}"                     # 128GB RAM이면 Q6_K/Q8_0 권장
OLLAMA_NAME="${OLLAMA_NAME:-aitg-sunhwa}"

echo "1) LoRA 병합"
python -m rewriter.merge_lora --base "$BASE" --adapter "$ADAPTER" --out "$MERGED"

echo "2) HF → GGUF(f16)"
python "$LLAMACPP/convert_hf_to_gguf.py" "$MERGED" \
  --outfile outputs/qwen-sunhwa-f16.gguf --outtype f16

echo "3) 양자화 ($QUANT)"
"$LLAMACPP/llama-quantize" outputs/qwen-sunhwa-f16.gguf \
  rewriter/qwen-sunhwa.gguf "$QUANT"

echo "4) Ollama 등록"
ollama create "$OLLAMA_NAME" -f rewriter/Modelfile

echo "✅ 완료: ollama run $OLLAMA_NAME"
echo "   백엔드 연결: OLLAMA_MODEL=$OLLAMA_NAME uvicorn app.main:app --reload"
