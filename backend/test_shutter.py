from fractions import Fraction

def format_shutter_speed(val):
    if not val:
        return None
    try:
        # If it's a very small float like 0.0016666, convert to fraction like 1/600
        if isinstance(val, float) and val < 1:
            frac = Fraction(val).limit_denominator(10000)
            return str(frac)
        # If it's a string, just clean it and check length
        val_str = str(val)
        if len(val_str) > 20: # DB limit is 20
             # Try to shorten if it's a long decimal
             if '.' in val_str:
                 try:
                     f = float(val_str)
                     if f < 1:
                         return str(Fraction(f).limit_denominator(10000))
                     else:
                         return f"{f:.1f}"
                 except:
                     pass
             return val_str[:20]
        return val_str
    except:
        return str(val)[:20]

test_vals = [
    0.004545454545454545,
    0.01,
    0.001,
    0.016666666666666666,
    0.00025,
    "0.004545454545454545"
]

for v in test_vals:
    print(f"Input: {v}, Output: {format_shutter_speed(v)}")
