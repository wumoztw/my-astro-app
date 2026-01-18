import os
import time
from kerykeion import AstrologicalSubject, KerykeionChartSVG

def draw_circular_chart(user_data):
    """
    Generates a circular astrology chart SVG using Kerykeion.
    """
    try:
        # Create a unique name to avoid browser caching
        timestamp = int(time.time())
        unique_name = f"UserBirthChart_{timestamp}"
        
        # Initialize AstrologicalSubject
        # Using utc_offset instead of tz (API v4.2.0+)
        subject = AstrologicalSubject(
            unique_name,
            year=int(user_data['year']),
            month=int(user_data['month']),
            day=int(user_data['day']),
            hour=int(user_data['hour']),
            minute=int(user_data['minute']),
            city=user_data.get('city', 'Taipei'),
            lat=float(user_data['lat']),
            lng=float(user_data['lng']),
            utc_offset=float(user_data['tz'])
        )
        
        # Set output directory to a local 'charts' folder
        output_dir = os.path.abspath("charts")
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        # Initialize KerykeionChartSVG
        chart = KerykeionChartSVG(subject, new_output_directory=output_dir)
        
        # Generate the SVG file
        chart.makeSVG()
        
        # Identify the generated filename
        filename = f"{unique_name}_Natal.svg"
        file_path = os.path.join(output_dir, filename)
        
        # Read the SVG content and return it directly
        if os.path.exists(file_path):
            with open(file_path, "r", encoding="utf-8") as f:
                svg_content = f.read()
            
            # Clean up the file after reading
            try:
                os.remove(file_path)
            except:
                pass
                
            return svg_content
        return None
        
    except Exception as e:
        print(f"Error in draw_circular_chart: {e}")
        return None
