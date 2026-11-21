from transformers import AutoTokenizer

# Define the three tokenizers
TOKENIZERS = {
    "BPE - GPT-2": "gpt2",
    "WordPiece - Multilingual BERT": "bert-base-multilingual-cased",
    "SentencePiece - XLM-R": "xlm-roberta-base"
}

# Input sentences in three languages
TEXTS = {
    "English": "Artificial intelligence is changing the world.",
    "Telugu": "కృత్రిమ మేధస్సు ప్రపంచాన్ని మారుస్తోంది.",
    "Hindi": "कृत्रिम बुद्धिमत्ता दुनिया को बदल रही है।"
}


# Load pretrained tokenizers
def load_tokenizers():
    loaded = {}

    for display_name, model_name in TOKENIZERS.items():
        print(f"Loading {display_name}...")
        loaded[display_name] = AutoTokenizer.from_pretrained(model_name)

    return loaded


# Compare tokenizers
def compare_tokenizers(loaded_tokenizers):

    for language, text in TEXTS.items():

        print("\n" + "=" * 75)
        print(f"LANGUAGE: {language}")
        print(f"INPUT TEXT: {text}")
        print("=" * 75)

        for tokenizer_name, tokenizer in loaded_tokenizers.items():

            encoded = tokenizer(
                text,
                add_special_tokens=True,
                truncation=False
            )

            token_ids = encoded["input_ids"]

            tokens = tokenizer.convert_ids_to_tokens(token_ids)

            print(f"\n{tokenizer_name}")
            print("Tokens     :", tokens)
            print("Token IDs  :", token_ids)
            print("Token count:", len(token_ids))


# Main function
def main():
    tokenizers = load_tokenizers()
    compare_tokenizers(tokenizers)


if __name__ == "__main__":
    main()
