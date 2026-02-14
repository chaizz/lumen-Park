from fractions import Fraction

from PIL import Image
from PIL.ExifTags import TAGS


def clean_string(val):
    if isinstance(val, str):
        return val.replace('\x00', '').strip()
    return val

def format_shutter_speed(val):
    if not val:
        return None
    try:
        f_val = None
        # Handle tuple/list (numerator, denominator)
        if isinstance(val, (tuple, list)) and len(val) == 2:
            if val[1] == 0: return "0"
            f_val = val[0] / val[1]
        else:
            # Try to convert to float
            try:
                f_val = float(val)
            except (ValueError, TypeError):
                # If conversion fails, maybe it's already a fraction string
                if isinstance(val, str) and '/' in val:
                     return val[:20]
                raise

        if f_val is not None:
            if 0 < f_val < 1:
                frac = Fraction(f_val).limit_denominator(10000)
                return str(frac)
            elif f_val == 0:
                return "0"
            else:
                if f_val.is_integer():
                    return str(int(f_val))
                return f"{f_val:.1f}".rstrip('0').rstrip('.')
    except Exception:
        pass
        
    return str(val)[:20]

def extract_exif(file_stream):
    exif_data = {}
    try:
        image = Image.open(file_stream)
        info = image._getexif()
        if info:
            for tag, value in info.items():
                decoded = TAGS.get(tag, tag)
                if decoded == "Make":
                    exif_data["camera_make"] = clean_string(str(value))
                elif decoded == "Model":
                    exif_data["camera_model"] = clean_string(str(value))
                elif decoded == "LensModel":
                    exif_data["lens"] = clean_string(str(value))
                elif decoded == "FNumber":
                    exif_data["aperture"] = float(value) if value else None
                elif decoded == "ExposureTime":
                    exif_data["shutter_speed"] = format_shutter_speed(value)
                elif decoded == "ISOSpeedRatings":
                    exif_data["iso"] = int(value)
                elif decoded == "FocalLength":
                    exif_data["focal_length"] = float(value) if value else None
                
    except Exception as e:
        print(f"Error extracting EXIF: {e}")
        
    return exif_data
