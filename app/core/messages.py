# app/core/messages.py

TRANSLATIONS = {
    "en": {
        "product_not_found": "Product not found",
        "price_greater_zero": "Price must be greater than zero",
    },
}


def get_message(key: str, lang: str = "en") -> str:
    lang_dict = TRANSLATIONS.get(lang, TRANSLATIONS["en"])
    return lang_dict.get(key, TRANSLATIONS["en"].get(key, key))
