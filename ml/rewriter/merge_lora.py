"""LoRA 어댑터를 베이스 모델에 병합 → 단일 HF 모델로 저장.

export_ollama.sh 의 1단계. 병합 모델을 GGUF 로 변환해 Ollama 에 올린다.

사용:
    python -m rewriter.merge_lora \
        --base Qwen/Qwen2.5-14B-Instruct \
        --adapter outputs/qwen-sunhwa-lora \
        --out outputs/qwen-sunhwa-merged
"""

from __future__ import annotations

import argparse


def main() -> None:
    ap = argparse.ArgumentParser(description="LoRA 병합")
    ap.add_argument("--base", default="Qwen/Qwen2.5-14B-Instruct")
    ap.add_argument("--adapter", default="outputs/qwen-sunhwa-lora")
    ap.add_argument("--out", default="outputs/qwen-sunhwa-merged")
    args = ap.parse_args()

    import torch
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer

    print(f"▶ base={args.base} + adapter={args.adapter}")
    base = AutoModelForCausalLM.from_pretrained(
        args.base, torch_dtype=torch.float16, device_map="cpu"
    )
    model = PeftModel.from_pretrained(base, args.adapter)
    model = model.merge_and_unload()
    model.save_pretrained(args.out, safe_serialization=True)
    AutoTokenizer.from_pretrained(args.base).save_pretrained(args.out)
    print(f"✅ 병합 모델 저장 → {args.out}")


if __name__ == "__main__":
    main()
