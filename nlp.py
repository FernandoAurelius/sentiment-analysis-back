from transformers import pipeline
classifier = pipeline("text-classification", model="openai-community/roberta-base-openai-detector")
classifier("A soccer game with multiple males playing. Some man are playing a sport")
