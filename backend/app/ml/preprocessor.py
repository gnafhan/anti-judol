"""
Text preprocessor for the ML pipeline.

This module defines custom transformers used in the scikit-learn 
pipeline for text classification. These classes must match the original
implementation used during model training for pickle compatibility.
"""

import re
import unicodedata
import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from app.ml.homoglyph_map import HOMOGLYPH_MAP


# Homoglyph mapping for Unicode normalization



class TextPreprocessor:
    """
    Preprocessing untuk menangani homoglyph dan variasi Unicode.
    """

    def normalize_homoglyph(self, text):
        """Konversi homoglyph Unicode ke karakter normal"""
        for homo, normal in HOMOGLYPH_MAP.items():
            text = text.replace(homo, normal)
        return text

    def normalize_unicode(self, text):
        """Normalisasi Unicode menggunakan NFKD"""
        return unicodedata.normalize('NFKD', text)

    def remove_extra_spaces(self, text):
        """Hapus spasi berlebih"""
        return re.sub(r'\s+', ' ', text).strip()

    def preprocess(self, text):
        """Pipeline preprocessing lengkap"""
        text = str(text).lower()
        text = self.normalize_homoglyph(text)
        text = self.normalize_unicode(text)
        text = self.remove_extra_spaces(text)
        return text


class AdditionalFeatures:
    """Ekstraksi fitur tambahan untuk deteksi spam"""

    def count_emoji(self, text):
        """Hitung jumlah emoji"""
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"
            "\U0001F300-\U0001F5FF"
            "\U0001F680-\U0001F6FF"
            "\U0001F1E0-\U0001F1FF"
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "]+",
            flags=re.UNICODE
        )
        return len(emoji_pattern.findall(text))

    def capital_ratio(self, text):
        """Rasio huruf kapital"""
        if len(text) == 0:
            return 0
        return sum(1 for c in text if c.isupper()) / len(text)

    def has_numbers_in_word(self, text):
        """Deteksi angka dalam kata (SLOT88, PLUTO88)"""
        pattern = r'[a-zA-Z]+\d+|\d+[a-zA-Z]+'
        return len(re.findall(pattern, text))

    def excessive_spacing(self, text):
        """Deteksi spasi berlebih antar karakter"""
        pattern = r'(\w\s){3,}'
        return len(re.findall(pattern, text))

    def extract_features(self, texts):
        """Ekstraksi semua fitur"""
        features = []
        for text in texts:
            features.append([
                self.count_emoji(text),
                self.capital_ratio(text),
                self.has_numbers_in_word(text),
                self.excessive_spacing(text)
            ])
        return np.array(features)


class AdditionalFeaturesTransformer(BaseEstimator, TransformerMixin):
    """Transformer untuk fitur tambahan"""

    def __init__(self):
        self.feature_extractor = AdditionalFeatures()

    def fit(self, X, y=None):
        return self

    def transform(self, X):
        return self.feature_extractor.extract_features(X)
