from django.shortcuts import render
from faker import Faker

# def generate_lorem_ipsum(paragraphs=3):
#     fake = Faker()
#     lorem_ipsum_text = fake.paragraphs(paragraphs)
#     return lorem_ipsum_text


def generate_lorem_ipsum(paragraphs=3):
    fake = Faker()
    lorem_ipsum_text = []
    for _ in range(paragraphs):
        for _ in range(paragraphs):
            paragraph = " ".join(fake.sentences(nb=5))
            lorem_ipsum_text.append(paragraph)
        lorem_ipsum_text.append('<br>')
    return "\n\n".join(lorem_ipsum_text)