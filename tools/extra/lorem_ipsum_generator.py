from django.shortcuts import render
from faker import Faker

def generate_lorem_ipsum(paragraphs=3):
    fake = Faker()
    lorem_ipsum_text = fake.paragraphs(paragraphs)
    return lorem_ipsum_text
