from fractions import Fraction

def format_shutter_speed(val):
    if not val:
        return None
    
    try:
        f_val = None
        # Handle tuple/list (numerator, denominator) which Pillow might return
        if isinstance(val, (tuple, list)) and len(val) == 2:
            if val[1] == 0: return "0"
            f_val = val[0] / val[1]
        else:
            # Try to convert to float (handles float, int, decimal strings)
            try:
                f_val = float(val)
            except (ValueError, TypeError):
                # Maybe it's already a fraction string like "1/100"
                if isinstance(val, str) and '/' in val:
                    return val[:20]
                raise

        if f_val is not None:
            # If it's a very small float < 1, convert to fraction
            if 0 < f_val < 1:
                # use limit_denominator to find close fraction
                frac = Fraction(f_val).limit_denominator(10000)
                return str(frac)
            elif f_val == 0:
                return "0"
            else:
                # If integer, return as int string
                if f_val.is_integer():
                    return str(int(f_val))
                # Otherwise keep up to 1 decimal place if needed, or just string
                # But usually shutter speeds >= 1 are integers like 1, 2, 5, 15...
                # except for like 1.5s, 2.5s etc.
                return f"{f_val:.1f}".rstrip('0').rstrip('.')
            
    except Exception as e:
        # print(f"Error: {e}")
        pass
        
    # Fallback: clean string and check length
    val_str = str(val)
    return val_str[:20]

test_vals = [
    0.004545454545454545, # Should be 1/220
    0.01, # 1/100
    0.001, # 1/1000
    0.016666666666666666, # 1/60
    "0.004545454545454545", # Should be 1/220
    "1/100", # Should be 1/100
    (1, 200), # Should be 1/200
    1.0, # 1
    30.0, # 30
    1.5, # 1.5
    "invalid", # invalid
    0, # 0
    None
]

for v in test_vals:
    print(f"Input: {v} ({type(v).__name__}), Output: {format_shutter_speed(v)}")
