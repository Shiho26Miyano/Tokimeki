import os
import pandas as pd
from datasets import Dataset
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
)
import torch

def fine_tune_bert(
    csv_path,
    text_column="text",
    label_column="label",
    model_name="bert-base-uncased",
    output_dir="fine_tuned_bert",
    num_labels=2,
    epochs=2,
    batch_size=8,
    learning_rate=2e-5,
):
    # 1. Load dataset
    df = pd.read_csv(csv_path)
    dataset = Dataset.from_pandas(df)

    # 2. Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(model_name, num_labels=num_labels)

    # 3. Tokenize
    def preprocess(examples):
        return tokenizer(examples[text_column], truncation=True, padding="max_length", max_length=128)
    tokenized = dataset.map(preprocess, batched=True)

    # 4. Training arguments
    training_args = TrainingArguments(
        output_dir=output_dir,
        num_train_epochs=epochs,
        per_device_train_batch_size=batch_size,
        per_device_eval_batch_size=batch_size,
        evaluation_strategy="epoch",
        save_strategy="epoch",
        learning_rate=learning_rate,
        logging_dir=f"{output_dir}/logs",
        logging_steps=10,
        load_best_model_at_end=True,
        metric_for_best_model="eval_loss",
    )

    # 5. Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized,
        eval_dataset=tokenized,  # For demo, use same data
    )

    # 6. Train
    trainer.train()
    trainer.save_model(output_dir)
    print(f"Model fine-tuned and saved to {output_dir}")

if __name__ == "__main__":
    # Example usage
    fine_tune_bert(
        csv_path="your_dataset.csv",  # CSV with 'text' and 'label' columns
        text_column="text",
        label_column="label",
        model_name="bert-base-uncased",
        output_dir="fine_tuned_bert",
        num_labels=2,
        epochs=2,
        batch_size=8,
        learning_rate=2e-5,
    ) 