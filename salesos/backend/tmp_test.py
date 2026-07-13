from domains.search.normalization.arabic_normalizer import ArabicSearchNormalizer
n = ArabicSearchNormalizer.default()
print("sukun:", repr(n.normalize('\u0645\u0650\u0646\u0652')))
print("conj:", repr(n.normalize('\u0634\u0631\u0643\u0629 \u0648 \u0645\u0624\u0633\u0633\u0629')))
