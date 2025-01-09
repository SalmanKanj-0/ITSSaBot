import openai
import logging
import os
# Initialize logging
logger = logging.getLogger(__name__)

# OpenAI Configuration
openai.api_key = os.environ.get("OPENAI_API_KEY")

def get_openai_response(user_message):
    """
    Queries OpenAI to get a response for the given user message.
    """
    try:
        logger.info("Querying OpenAI with user message: %s", user_message)
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are a helpful IT assistant answering FAQs on MacBook devices.",
                },
                {"role": "user", "content": user_message},
            ],
        )
        result = response["choices"][0]["message"]["content"]
        logger.info("OpenAI response: %s", result)
        return result
    except Exception as e:
        logger.error("Error querying OpenAI: %s", str(e))
        return f"Error: {str(e)}"

def summarize_message(user_message):
    """
    Uses OpenAI to summarize the user's message for the Jira ticket summary.
    """
    try:
        prompt = (
            "Summarize the following user message into a concise summary suitable for a Jira ticket title. "
            "The summary should be clear and capture the main issue without losing essential details.\n\n"
            "User Message:\n"
            f"{user_message}\n\n"
            "Summary:"
        )

        logger.info("Sending prompt to OpenAI for message summarization.")

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {
                    "role": "system",
                    "content": "You are an assistant that summarizes user messages for Jira ticket titles.",
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,  # Low temperature for more deterministic summaries
        )

        summary = response["choices"][0]["message"]["content"].strip()
        logger.info(f"OpenAI generated summary: {summary}")

        return summary
    except Exception as e:
        logger.error(f"Error summarizing message with OpenAI: {e}")
        return "Support Request"

#def train_model_on_confluence(confluence_pages, model, tokenizer):
    """Train a model using content from Confluence pages."""
    from transformers import Trainer, TrainingArguments
    import datasets

    # Prepare dataset from Confluence pages
    data = datasets.Dataset.from_dict({"text": confluence_pages})
    tokenized_data = data.map(lambda x: tokenizer(x["text"], truncation=True, padding="max_length"), batched=True)
    
    # Training arguments
    training_args = TrainingArguments(
        output_dir="./results",
        evaluation_strategy="epoch",
        learning_rate=2e-5,
        per_device_train_batch_size=8,
        num_train_epochs=3,
        weight_decay=0.01,
        save_total_limit=2
    )

    # Trainer setup
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_data
    )

    # Train the model
    trainer.train()
    return trainer
