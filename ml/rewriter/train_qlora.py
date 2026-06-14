"""2단계 순화 LLM — Qwen2.5-14B QLoRA 파인튜닝 (확정 스택).

QLoRA 4-bit, r=16, alpha=32 (CLAUDE.md 기준선). 학습 데이터는 합성 순화 쌍
(synth.jsonl). 결과 LoRA 어댑터를 저장 → export_ollama 로 병합·GGUF·Ollama 등록.

⚠️ 실제 학습은 GPU(맥북 MPS/Colab A100) 필요. 역할 분담상 사용자가 실행한다.
    (Apple Silicon 은 bitsandbytes 4-bit 미지원 → Colab/CUDA 권장, 또는 mlx-lm 경로)

사용:
    python -m rewriter.train_qlora \
        --data ../data/processed/synth.jsonl \
        --base Qwen/Qwen2.5-14B-Instruct \
        --out outputs/qwen-sunhwa-lora
"""

from __future__ import annotations

import argparse

from .dataset import build_dataset


def main() -> None:
    ap = argparse.ArgumentParser(description="순화 LLM QLoRA 파인튜닝")
    ap.add_argument("--data", default="../data/processed/synth.jsonl")
    ap.add_argument("--base", default="Qwen/Qwen2.5-14B-Instruct")
    ap.add_argument("--out", default="outputs/qwen-sunhwa-lora")
    ap.add_argument("--epochs", type=float, default=3.0)
    ap.add_argument("--batch-size", type=int, default=1)
    ap.add_argument("--grad-accum", type=int, default=8)
    ap.add_argument("--lr", type=float, default=2e-4)
    ap.add_argument("--max-seq", type=int, default=1024)
    args = ap.parse_args()

    import torch
    from peft import LoraConfig
    from transformers import (
        AutoModelForCausalLM,
        AutoTokenizer,
        BitsAndBytesConfig,
    )
    from trl import SFTConfig, SFTTrainer

    # 1) 데이터
    ds = build_dataset(args.data)
    print(f"▶ 학습 쌍: {len(ds)}건 | base={args.base}")

    # 2) 4-bit 양자화 로드 (QLoRA)
    bnb = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    tokenizer = AutoTokenizer.from_pretrained(args.base)
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token
    model = AutoModelForCausalLM.from_pretrained(
        args.base,
        quantization_config=bnb,
        torch_dtype=torch.bfloat16,
        device_map="auto",
    )

    # 3) LoRA (r=16, alpha=32 — 확정 기준선)
    peft_config = LoraConfig(
        r=16,
        lora_alpha=32,
        lora_dropout=0.05,
        bias="none",
        task_type="CAUSAL_LM",
        target_modules=[
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ],
    )

    # 4) SFT (chat 템플릿 자동 적용)
    sft_config = SFTConfig(
        output_dir=args.out,
        num_train_epochs=args.epochs,
        per_device_train_batch_size=args.batch_size,
        gradient_accumulation_steps=args.grad_accum,
        learning_rate=args.lr,
        max_seq_length=args.max_seq,
        logging_steps=10,
        save_strategy="epoch",
        bf16=True,
        report_to=[],
    )
    trainer = SFTTrainer(
        model=model,
        args=sft_config,
        train_dataset=ds,
        peft_config=peft_config,
        processing_class=tokenizer,
    )

    trainer.train()
    trainer.save_model(args.out)
    tokenizer.save_pretrained(args.out)
    print(f"✅ LoRA 어댑터 저장 → {args.out}")
    print("다음: rewriter/export_ollama.sh 로 병합 → GGUF → ollama create")


if __name__ == "__main__":
    main()
