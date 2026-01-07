"""UI display components"""
import streamlit as st

def display_nutrition_card(nutrition_data: dict):
    """Display visual nutrition card"""
    if not nutrition_data.get('calories'):
        return
    
    st.markdown('<div class="nutrition-card-pro animate-fade-in"><h3>📊 Nutritional Breakdown</h3><div class="macro-grid-pro">', unsafe_allow_html=True)
    
    macros = [
        ("🔥", nutrition_data.get('calories', 'N/A'), "Calories", "kcal"),
        ("💪", nutrition_data.get('protein', 'N/A'), "Protein", "g"),
        ("🌾", nutrition_data.get('carbs', 'N/A'), "Carbs", "g"),
        ("🥑", nutrition_data.get('fat', 'N/A'), "Fat", "g")
    ]
    
    for emoji, value, label, unit in macros:
        unit_display = unit if value != 'N/A' else ''
        st.markdown(f'''
        <div class="macro-item-pro">
            <div style="font-size: 2rem; margin-bottom: 0.5rem;">{emoji}</div>
            <span class="macro-value-pro">{value}{unit_display}</span>
            <span class="macro-label-pro">{label}</span>
        </div>
        ''', unsafe_allow_html=True)
    
    st.markdown("</div></div>", unsafe_allow_html=True)

def display_health_score(score: int):
    """Display health score with circular progress"""
    if not score:
        return
    
    if score >= 80:
        color, rating, emoji = "#10b981", "Excellent", "🌟"
    elif score >= 60:
        color, rating, emoji = "#f59e0b", "Good", "👍"
    else:
        color, rating, emoji = "#ef4444", "Fair", "⚠️"
    
    circumference = 377
    offset = circumference - (circumference * score / 100)
    
    st.markdown(f'''
    <div class="health-score-container animate-fade-in">
        <div class="score-circle">
            <svg viewBox="0 0 120 120">
                <circle class="score-circle-bg" cx="60" cy="60" r="54"/>
                <circle class="score-circle-progress" cx="60" cy="60" r="54"
                    style="stroke: {color}; stroke-dashoffset: {offset};"/>
            </svg>
            <div class="score-text">{score}</div>
        </div>
        <div class="score-details">
            <h4>{emoji} Health Score: {rating}</h4>
            <p>This food scores {score}/100 on our health index</p>
        </div>
    </div>
    ''', unsafe_allow_html=True)

def display_dietary_badges(dietary_info: dict):
    """Display dietary compatibility badges"""
    if not dietary_info:
        return
    
    st.markdown('<div class="dietary-badges-pro">', unsafe_allow_html=True)
    
    badge_emojis = {
        'Vegan': '🌱', 'Vegetarian': '🥗', 'Keto-Friendly': '🥓',
        'Gluten-Free': '🌾', 'Dairy-Free': '🥛', 'High-Protein': '💪'
    }
    
    for diet, compatible in dietary_info.items():
        badge_class = "badge-yes-pro" if compatible else "badge-no-pro"
        icon = "✓" if compatible else "✗"
        emoji = badge_emojis.get(diet, '🔸')
        st.markdown(f'<span class="badge-pro {badge_class}">{icon} {emoji} {diet}</span>', unsafe_allow_html=True)
    
    st.markdown('</div>', unsafe_allow_html=True)
