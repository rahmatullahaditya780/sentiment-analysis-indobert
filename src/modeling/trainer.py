"""
Fase 4 — Loop fine-tuning IndoBERT (HuggingFace Trainer).

Komponen utama:
- `compute_metrics`         : akurasi + precision/recall/F1 (macro), metrik
                              utama = macro F1 (FR-4.8, target >= 85%).
- `WeightedLossTrainer`     : subclass `Trainer` yang menerapkan class weight
                              pada CrossEntropyLoss (wajib karena imbalance > 15%).
- `build_training_arguments`: TrainingArguments dengan LR scheduler linear +
                              warmup (FR-4.5) dan checkpoint best-by-macro-F1.
- `train_model`             : orkestrasi training satu konfigurasi lengkap
                              dengan early stopping (FR-4.4) + simpan model.

Semua impor `torch`/`transformers` bersifat LAZY (di dalam fungsi) supaya modul
bisa diimpor lokal tanpa dependency berat. Eksekusi nyata di Google Colab.
"""

from __future__ import annotations

from pathlib import Path

from src.modeling.config import (
    ID2LABEL,
    LABEL2ID,
    NUM_LABELS,
    TRAINING_LOG_CSV,
    TrainingConfig,
    ensure_output_dirs,
)


# ── Metrik ────────────────────────────────────────────────────────────────────
def compute_metrics(eval_pred):
    """Hitung metrik klasifikasi dari output Trainer.

    Mengembalikan dict: accuracy, precision_macro, recall_macro, f1_macro.
    `f1_macro` adalah metrik penentu best model & gate Fase 4.
    """
    import numpy as np
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support

    logits, labels = eval_pred
    preds = np.argmax(logits, axis=-1)
    precision, recall, f1, _ = precision_recall_fscore_support(
        labels, preds, average="macro", zero_division=0
    )
    return {
        "accuracy": accuracy_score(labels, preds),
        "precision_macro": precision,
        "recall_macro": recall,
        "f1_macro": f1,
    }


# ── Model loader ──────────────────────────────────────────────────────────────
def load_model(config: TrainingConfig):
    """Muat IndoBERT untuk klasifikasi sequence (num_labels=NUM_LABELS).

    Menyetel dropout sesuai config dan menanam mapping label<->id ke config
    model (berguna untuk inferensi Fase 6).
    """
    from transformers import AutoModelForSequenceClassification

    model = AutoModelForSequenceClassification.from_pretrained(
        config.model_name,
        num_labels=NUM_LABELS,
        id2label=ID2LABEL,
        label2id=LABEL2ID,
        hidden_dropout_prob=config.dropout_rate,
        attention_probs_dropout_prob=config.dropout_rate,
    )
    return model


# ── Trainer dengan class weight ───────────────────────────────────────────────
def make_weighted_trainer_cls(class_weights):
    """Buat subclass Trainer yang memakai class weight pada loss.

    `class_weights`: list float terurut id (lihat data.compute_class_weights).
    Dikembalikan sebagai factory agar bobot ter-bind tanpa global state.
    """
    import torch
    from transformers import Trainer

    weight_tensor = torch.tensor(class_weights, dtype=torch.float)

    class WeightedLossTrainer(Trainer):
        def compute_loss(self, model, inputs, return_outputs=False, **kwargs):
            labels = inputs.pop("labels")
            outputs = model(**inputs)
            logits = outputs.logits
            loss_fct = torch.nn.CrossEntropyLoss(
                weight=weight_tensor.to(logits.device)
            )
            loss = loss_fct(logits.view(-1, NUM_LABELS), labels.view(-1))
            return (loss, outputs) if return_outputs else loss

    return WeightedLossTrainer


# ── TrainingArguments ─────────────────────────────────────────────────────────
def build_training_arguments(config: TrainingConfig, output_dir: str | Path):
    """Bangun TrainingArguments: LR scheduler linear+warmup, best-by-f1_macro.

    Evaluasi & checkpoint per epoch; best model dimuat ulang di akhir
    berdasarkan f1_macro (FR-4.8).
    """
    from transformers import TrainingArguments

    return TrainingArguments(
        output_dir=str(output_dir),
        num_train_epochs=config.num_epochs,
        per_device_train_batch_size=config.batch_size,
        per_device_eval_batch_size=config.batch_size,
        learning_rate=config.learning_rate,
        weight_decay=config.weight_decay,
        warmup_steps=config.warmup_steps,
        lr_scheduler_type="linear",  # linear decay with warmup (FR-4.5)
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1_macro",
        greater_is_better=True,
        save_total_limit=1,
        logging_strategy="epoch",
        seed=config.seed,
        report_to="none",
    )


# ── Orkestrasi training ───────────────────────────────────────────────────────
def train_model(
    config: TrainingConfig,
    train_dataset,
    eval_dataset,
    class_weights,
    output_dir: str | Path,
    tokenizer=None,
    save_model: bool = False,
):
    """Latih satu konfigurasi penuh dan kembalikan (trainer, metrics).

    - Early stopping patience dari config (FR-4.4).
    - Class weight diterapkan di loss (imbalance > 15%).
    - `metrics` adalah hasil evaluasi best model pada eval_dataset.
    - Jika save_model=True, simpan model + tokenizer ke output_dir.
    """
    from transformers import EarlyStoppingCallback

    model = load_model(config)
    args = build_training_arguments(config, output_dir)
    trainer_cls = make_weighted_trainer_cls(class_weights)

    trainer = trainer_cls(
        model=model,
        args=args,
        train_dataset=train_dataset,
        eval_dataset=eval_dataset,
        compute_metrics=compute_metrics,
        callbacks=[
            EarlyStoppingCallback(early_stopping_patience=config.early_stopping_patience)
        ],
    )

    trainer.train()
    metrics = trainer.evaluate()

    if save_model:
        trainer.save_model(str(output_dir))
        if tokenizer is not None:
            tokenizer.save_pretrained(str(output_dir))

    return trainer, metrics


# ── Ekspor riwayat loss (untuk learning curve Fase 5, FR-5.6) ─────────────────
def export_loss_history_csv(trainer, path=TRAINING_LOG_CSV):
    """Tulis loss per epoch (train & validation) ke CSV untuk learning curve.

    Parse `trainer.state.log_history` (HF Trainer) menjadi baris per epoch:
    kolom epoch, train_loss, val_loss. Dipakai Fase 5 (`visualizer.plot_learning_curve`)
    karena `save_model()` TIDAK menyertakan trainer_state.json. Panggil setelah
    `train_model(...)`. Mengembalikan path file yang ditulis.
    """
    import csv

    by_epoch: dict[float, dict] = {}
    for entry in trainer.state.log_history:
        epoch = entry.get("epoch")
        if epoch is None:
            continue
        bucket = by_epoch.setdefault(epoch, {})
        if "loss" in entry:
            bucket["train_loss"] = entry["loss"]
        if "eval_loss" in entry:
            bucket["val_loss"] = entry["eval_loss"]

    rows = [
        (round(ep, 2), v["train_loss"], v["val_loss"])
        for ep, v in sorted(by_epoch.items())
        if "train_loss" in v and "val_loss" in v
    ]

    from pathlib import Path

    path = Path(path)
    ensure_output_dirs()
    with path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["epoch", "train_loss", "val_loss"])
        writer.writerows(rows)
    return path
