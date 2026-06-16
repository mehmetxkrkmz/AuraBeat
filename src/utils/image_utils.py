from PyQt6.QtGui import QImage, QColor
from PyQt6.QtCore import Qt

def get_dominant_colors(qimage: QImage):
    """
    Returns a tuple of two QColors (primary, secondary) representing the 
    most dominant distinct colors in the image using a clustering approach.
    """
    default_c1 = QColor(13, 17, 23)
    default_c2 = QColor(48, 54, 61)
    
    if qimage.isNull():
        return (default_c1, default_c2)
    
    # Scale down the image drastically for performance
    scaled = qimage.scaled(50, 50, Qt.AspectRatioMode.IgnoreAspectRatio, Qt.TransformationMode.FastTransformation)
    
    # Bucket colors (group similar colors together)
    buckets = {}
    
    for y in range(scaled.height()):
        for x in range(scaled.width()):
            color = QColor(scaled.pixel(x, y))
            # skip completely black or white or very dark/light pixels
            if color.lightness() < 30 or color.lightness() > 220:
                continue
            
            # Increase saturation slightly to make the color pop
            h, s, l, a = color.getHsl()
            s = min(255, int(s * 1.5))
            color.setHsl(h, s, l, a)
            
            # Create a bucket key by grouping RGB values into bins of 32
            r, g, b = color.red(), color.green(), color.blue()
            bin_size = 32
            key = (r // bin_size, g // bin_size, b // bin_size)
            
            if key not in buckets:
                buckets[key] = []
            buckets[key].append(color)
            
    if not buckets:
        return (default_c1, default_c2)
        
    # Sort buckets by number of pixels
    sorted_buckets = sorted(buckets.values(), key=len, reverse=True)
    
    # Function to average a bucket
    def average_bucket(bucket):
        r_tot = sum(p.red() for p in bucket)
        g_tot = sum(p.green() for p in bucket)
        b_tot = sum(p.blue() for p in bucket)
        return QColor(r_tot // len(bucket), g_tot // len(bucket), b_tot // len(bucket))
        
    primary = average_bucket(sorted_buckets[0])
    
    if len(sorted_buckets) == 1:
        return (primary, primary.darker(150))
        
    # Find the second color: iterate through buckets to find one that is sufficiently different from primary
    secondary = None
    for bucket in sorted_buckets[1:]:
        candidate = average_bucket(bucket)
        dist = (candidate.red() - primary.red())**2 + (candidate.green() - primary.green())**2 + (candidate.blue() - primary.blue())**2
        if dist > 8000: # Threshold for being visually distinct
            secondary = candidate
            break
            
    if secondary is None:
        # If no bucket is distinct enough, just use the second largest bucket and mix it
        secondary = average_bucket(sorted_buckets[1])
        mix_r = (secondary.red() * 2 + primary.red()) // 3
        mix_g = (secondary.green() * 2 + primary.green()) // 3
        mix_b = (secondary.blue() * 2 + primary.blue()) // 3
        secondary = QColor(mix_r, mix_g, mix_b)
        
    return (primary, secondary)

def get_dominant_color(qimage: QImage) -> QColor:
    c1, c2 = get_dominant_colors(qimage)
    return c1
