# Allowed quality values for climate data
QUALITY_VALUES = ('excellent', 'good', 'questionable', 'poor')

# Quality weights for summary/statistics calculations
QUALITY_WEIGHTS = {
    'excellent': 1.0,
    'good': 0.8,
    'questionable': 0.5,
    'poor': 0.3
}