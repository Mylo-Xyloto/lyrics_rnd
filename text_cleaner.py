import re


def clean_text(text):
    text = text.strip()
    text = re.sub(r",", "", text)
    text = re.sub(r"-", " ", text)
    text = re.sub(r"\/", " ", text)
    text = re.sub(r"\.", "", text)
    text = re.sub(r":", " ", text)
    text = re.sub(r"'", " ", text)
    text = re.sub(r"।", "", text)
    text = re.sub(r"’", " ", text)
    
    text = text.split('\n')
    refined_text = ""
    for line in text:
        if line:
            refined_text += line.strip() + ' '

    return refined_text
