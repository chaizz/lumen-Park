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
