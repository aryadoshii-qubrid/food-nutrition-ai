"""Parse AI responses for structured data"""
import re

def parse_nutrition_data(response_text: str) -> dict:
    """
    Extract structured nutrition data from AI response
    
    Args:
        response_text: Raw AI response text
        
    Returns:
        Dictionary with parsed nutrition data
    """
    data = {
        'calories': None,
        'protein': None,
        'carbs': None,
        'fat': None,
        'fiber': None,
        'health_score': None,
        'dietary': {},
        'dish_name': None
    }
    
    # Extraction patterns
    patterns = {
        'calories': r'Calories:\s*(\d+)\s*kcal',
        'protein': r'Protein:\s*(\d+\.?\d*)g',
        'carbs': r'Carbohydrates:\s*(\d+\.?\d*)g',
        'fat': r'Fat:\s*(\d+\.?\d*)g',
        'fiber': r'Fiber:\s*(\d+\.?\d*)g',
        'health_score': r'HEALTH SCORE:\s*(\d+)/100',
        'dish_name': r'Dish Name:\s*(.+?)(?:\n|-)'
    }
    
    # Extract values
    for key, pattern in patterns.items():
        match = re.search(pattern, response_text)
        if match:
            value = match.group(1).strip()
            if key == 'dish_name':
                data[key] = value
            elif key in ['protein', 'carbs', 'fat', 'fiber']:
                data[key] = float(value)
            else:
                data[key] = int(value)
    
    # Extract dietary compatibility
    dietary_checks = ['Vegan', 'Vegetarian', 'Keto-Friendly', 'Gluten-Free', 'Dairy-Free', 'High-Protein']
    for check in dietary_checks:
        match = re.search(f'{check}:\\s*(Yes|No)', response_text)
        if match:
            data['dietary'][check] = match.group(1) == 'Yes'
    
    return data
