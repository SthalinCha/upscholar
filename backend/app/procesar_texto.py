import re
from nltk.corpus import stopwords
import nltk
from unicodedata import normalize
import unicodedata
nltk.download("stopwords", quiet=True)

def normalizar_y_filtrar(texto):
    if not texto:
        return []

    texto = str(texto).lower()

    # --- Normalización para conservar ñ y eliminar tildes ---
    texto = unicodedata.normalize('NFD', texto)
    texto = texto.replace('ñ', '\001')                     # proteger la ñ
    texto = re.sub(r'[\u0300-\u036f]', '', texto)         # eliminar tildes
    texto = texto.replace('\001', 'ñ')                    # restaurar ñ

    # --- Separar números de letras ---
    texto = re.sub(r'(\d+)([a-zñ]+)', r'\1 \2', texto)
    texto = re.sub(r'([a-zñ]+)(\d+)', r'\1 \2', texto)

    # --- Mantener solo letras, números y espacios ---
    texto = re.sub(r'[^a-zñ0-9\s]', ' ', texto)

    # Tokenización
    tokens = texto.split()

    # Stopwords español + inglés
    stop = set(stopwords.words("english")) | set(stopwords.words("spanish"))

    return [t for t in tokens if t not in stop and len(t) > 1]
    
def aplicar_stemming(lista_de_listas):
    stemmer = nltk.PorterStemmer()
    return [[stemmer.stem(t) for t in tokens] for tokens in lista_de_listas]
