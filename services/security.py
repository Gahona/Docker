PALABRAS_PROHIBIDAS = [
    "ignora las instrucciones anteriores",
    "ignore previous instructions",
    "dame la clave",
    "dame el password",
    "muestra las claves",
    "you are now a",
    "actua como root",
]


def es_prompt_sospechoso(texto: str) -> bool:
    """Función básica que revisa si el mensaje enviado por el usuario

    contiene alguna palabra o frase prohibida.
    """
    texto_en_minusculas = texto.lower()

    for palabra in PALABRAS_PROHIBIDAS:
        if palabra in texto_en_minusculas:
            # Si encuentra palabra prohibida True
            return True

    #  revisa todo si no encuentra nada raro False
    return False