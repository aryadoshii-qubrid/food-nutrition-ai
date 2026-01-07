"""
NutriVision AI - Food Nutrition Analyzer
Main Streamlit Application
"""
import streamlit as st
from PIL import Image
import time

from config import Config
from utils import (
    call_qubrid_api,
    call_qubrid_api_stream,
    encode_image_to_base64,
    parse_nutrition_data,
    display_nutrition_card,
    display_health_score,
    display_dietary_badges
)
from prompts import DETAILED_NUTRITION_PROMPT

Config.validate()

st.set_page_config(
    page_title=Config.PAGE_TITLE,
    page_icon=Config.PAGE_ICON,
    layout="wide",
    initial_sidebar_state="expanded"
)

def load_css():
    """Load custom CSS styling"""
    try:
        with open('assets/premium_style.css') as f:
            st.markdown(f'<style>{f.read()}</style>', unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning("⚠️ CSS file not found.")

load_css()

def init_session_state():
    """Initialize session state variables"""
    defaults = {
        "messages": [],
        "uploaded_image": None,
        "image_base64": None,
        "nutrition_data": {},
        "user_goal": "General Health",
        "analyzed": False,
        "analysis_result": None,
        "streaming_enabled": True,
        "session_history": [],
        "analyzing": False,
        "dish_name": None
    }
    
    for key, default in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default

init_session_state()

st.markdown('''
<div class="hero-header animate-fade-in">
    <h1>🍽️ NutriVision AI</h1>
    <p>Your AI-Powered Nutrition Analysis Companion</p>
    <div class="hero-badge">⚡ Powered by Advanced Vision AI</div>
</div>
''', unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### ⚙️ Settings")
    
    st.session_state.user_goal = st.selectbox(
        "🎯 Your Goal",
        ["General Health", "Weight Loss", "Muscle Gain", "Maintenance", "Athletic Performance"]
    )
    
    st.session_state.streaming_enabled = st.toggle(
        "⚡ Enable Streaming",
        value=st.session_state.streaming_enabled,
        help="Stream responses in real-time"
    )
    
    st.markdown("---")
    st.markdown("### 📸 Upload Food Image")
    
    uploaded_file = st.file_uploader("Drag & drop or browse", type=["jpg", "jpeg", "png"])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded", use_column_width=True)
        
        if st.session_state.uploaded_image is None or st.session_state.image_base64 is None:
            st.session_state.uploaded_image = image
            st.session_state.image_base64 = encode_image_to_base64(image)
            st.session_state.analyzed = False
            st.success("✅ Image uploaded!")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🗑️ Clear", use_container_width=True):
            st.session_state.messages = []
            st.session_state.nutrition_data = {}
            st.session_state.analyzed = False
            st.session_state.analysis_result = None
            st.session_state.analyzing = False
            st.rerun()
    with col2:
        if st.button("🔄 New", use_container_width=True):
            for key in ["messages", "uploaded_image", "image_base64", "nutrition_data", "analysis_result"]:
                st.session_state[key] = [] if key == "messages" else {} if key == "nutrition_data" else None
            st.session_state.analyzed = False
            st.session_state.analyzing = False
            st.rerun()
    
    st.markdown("---")
    st.markdown("### 📈 Session Stats")
    st.markdown(f'''
    <div class="metric-card animate-fade-in">
        <div class="metric-value">{len(st.session_state.messages)}</div>
        <div class="metric-label">Messages</div>
    </div>
    <div class="metric-card animate-fade-in">
        <div class="metric-value">{len(st.session_state.session_history)}</div>
        <div class="metric-label">Analyses</div>
    </div>
    <div class="metric-card animate-fade-in">
        <div class="metric-value">{st.session_state.user_goal.split()[0]}</div>
        <div class="metric-label">Goal</div>
    </div>
    ''', unsafe_allow_html=True)
    
    if st.session_state.session_history:
        st.markdown("---")
        st.markdown("### 📜 Session History")
        with st.expander("View Past Analyses"):
            for idx, history in enumerate(reversed(st.session_state.session_history)):
                st.markdown(f"**{idx + 1}.** {history['dish_name'] or 'Unknown Food'}")
                st.caption(f"🕒 {history['timestamp']}")
    
    st.markdown("---")
    st.markdown('''
    <div style="text-align: center; padding: 1rem;">
        <p style="color: #64748b; font-size: 0.85rem; margin: 0;">
            <strong>Built by Arya</strong><br>
            <span style="opacity: 0.7;">QubridAI Intern Project</span>
        </p>
    </div>
    ''', unsafe_allow_html=True)

if not st.session_state.uploaded_image:
    col1, col2, col3 = st.columns(3)
    features = [
        ("🔍", "Instant Analysis", "Get detailed nutritional breakdown in seconds"),
        ("🎯", "Personalized Advice", "Recommendations tailored to your goals"),
        ("💬", "Smart Conversations", "Ask anything about your food")
    ]
    
    for col, (emoji, title, desc) in zip([col1, col2, col3], features):
        with col:
            st.markdown(f'''
            <div class="glass-card-premium animate-fade-in">
                <div style="font-size: 3rem; text-align: center; margin-bottom: 1rem;">{emoji}</div>
                <h3 style="text-align: center; color: #0f172a; margin-bottom: 0.5rem;">{title}</h3>
                <p style="text-align: center; color: #64748b; font-size: 0.95rem; line-height: 1.6;">{desc}</p>
            </div>
            ''', unsafe_allow_html=True)
    
    st.markdown('''
    <div class="glass-card-premium" style="text-align: center; margin-top: 2rem;">
        <h2 style="color: #6366f1; margin-bottom: 1rem;">👈 Upload an image to get started!</h2>
        <p style="color: #64748b; font-size: 1.1rem;">Take a photo of any food and discover its nutritional secrets</p>
    </div>
    ''', unsafe_allow_html=True)

else:
    st.markdown("### 🔍 Food Analysis")
    
    if not st.session_state.analyzed and not st.session_state.analyzing:
        st.info("📸 Image uploaded! Click below to analyze.")
        
        if st.button("🚀 Analyze This Food", type="primary", use_container_width=True):
            st.session_state.analyzing = True
            st.rerun()
    
    if st.session_state.analyzing and not st.session_state.analyzed:
        with st.spinner("🔍 Analyzing food image..."):
            try:
                analysis_prompt = f"{DETAILED_NUTRITION_PROMPT}\n\nUser Goal: {st.session_state.user_goal}"
                
                api_messages = [{
                    "role": "user",
                    "content": analysis_prompt,
                    "image": st.session_state.image_base64
                }]
                
                start_time = time.time()
                response = call_qubrid_api(api_messages)
                end_time = time.time()
                
                if response:
                    st.session_state.analysis_result = response
                    st.session_state.analyzed = True
                    st.session_state.analyzing = False
                    
                    nutrition_data = parse_nutrition_data(response)
                    st.session_state.nutrition_data = nutrition_data
                    st.session_state.dish_name = nutrition_data.get('dish_name', 'Unknown Food')
                    
                    response_length = len(response)
                    estimated_tokens = response_length // 4
                    tokens_per_second = estimated_tokens / (end_time - start_time) if (end_time - start_time) > 0 else 0
                    
                    st.session_state.session_history.append({
                        'dish_name': nutrition_data.get('dish_name', 'Unknown Food'),
                        'timestamp': time.strftime("%Y-%m-%d %H:%M:%S"),
                        'response_time': f"{end_time - start_time:.2f}s",
                        'tokens': estimated_tokens,
                        'tps': f"{tokens_per_second:.2f}"
                    })
                    
                    st.markdown(f"""
                    <div style="
                        background: rgba(255, 255, 255, 0.95);
                        border-radius: 12px;
                        padding: 1.5rem;
                        margin: 1rem 0;
                        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
                        border: 1px solid rgba(0, 0, 0, 0.05);
                    ">
                        <div style="text-align: center; margin-bottom: 1rem;">
                            <span style="font-size: 1.1rem; font-weight: 600; color: #10b981;">
                                ✅ Analysis Complete!
                            </span>
                        </div>
                        <div style="
                            display: grid;
                            grid-template-columns: repeat(3, 1fr);
                            gap: 1.5rem;
                            text-align: center;
                        ">
                            <div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #6366f1; margin-bottom: 0.25rem;">
                                    {estimated_tokens}
                                </div>
                                <div style="font-size: 0.85rem; color: #64748b; font-weight: 500; text-transform: uppercase;">
                                    Tokens
                                </div>
                            </div>
                            <div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #10b981; margin-bottom: 0.25rem;">
                                    {end_time - start_time:.2f}s
                                </div>
                                <div style="font-size: 0.85rem; color: #64748b; font-weight: 500; text-transform: uppercase;">
                                    Response Time
                                </div>
                            </div>
                            <div>
                                <div style="font-size: 1.8rem; font-weight: 800; color: #f59e0b; margin-bottom: 0.25rem;">
                                    {tokens_per_second:.1f}
                                </div>
                                <div style="font-size: 0.85rem; color: #64748b; font-weight: 500; text-transform: uppercase;">
                                    Tokens/sec
                                </div>
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    st.rerun()
                else:
                    st.session_state.analyzing = False
                    st.error("Failed to analyze. Please try again.")
                    
            except Exception as e:
                st.session_state.analyzing = False
                st.error(f"❌ Error: {str(e)}")
    
    if st.session_state.analyzed and st.session_state.analysis_result:
        if hasattr(st.session_state, 'dish_name') and st.session_state.dish_name:
            st.markdown(f"""
            <div style="
                background: rgba(255, 255, 255, 0.95);
                backdrop-filter: blur(20px);
                border-radius: 16px;
                padding: 1.5rem;
                margin: 1rem 0;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.05);
                text-align: center;
            ">
                <h2 style="margin: 0; font-size: 2rem; font-weight: 800; color: #6366f1;">
                    🍽️ {st.session_state.dish_name}
                </h2>
            </div>
            """, unsafe_allow_html=True)
        
        if st.session_state.nutrition_data and st.session_state.nutrition_data.get('calories'):
            display_nutrition_card(st.session_state.nutrition_data)
            
            if st.session_state.nutrition_data.get('health_score'):
                display_health_score(st.session_state.nutrition_data['health_score'])
            
            if st.session_state.nutrition_data.get('dietary'):
                st.markdown("#### 🏷️ Dietary Compatibility")
                display_dietary_badges(st.session_state.nutrition_data['dietary'])
        
        st.markdown("""
        <style>
        div[data-testid="stExpander"] details summary {
            font-size: 1.3rem !important;
            font-weight: 700 !important;
            padding: 1.2rem !important;
            background: rgba(255, 255, 255, 0.95) !important;
            border-radius: 12px !important;
            text-align: center !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        with st.expander("📋 View Full Analysis", expanded=False):
            st.markdown(f"""
            <div style="
                background: white;
                padding: 2.5rem;
                border-radius: 16px;
                box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
                border: 1px solid rgba(0, 0, 0, 0.05);
                font-size: 1.05rem;
                line-height: 1.8;
                color: #1e293b;
            ">
                {st.session_state.analysis_result}
            </div>
            """, unsafe_allow_html=True)
        
        # EXPORT & SHARE SECTION
        st.markdown("---")
        st.markdown("### 📤 Export & Share")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📄 Download PDF Report", use_container_width=True):
                from utils.export_utils import create_pdf_report, get_download_link
                
                pdf_buffer = create_pdf_report(
                    st.session_state.nutrition_data,
                    st.session_state.dish_name or "Food Analysis",
                    st.session_state.analysis_result,
                    st.session_state.user_goal
                )
                
                filename = f"nutrition_report_{st.session_state.dish_name.replace(' ', '_').lower()}.pdf"
                st.markdown(get_download_link(pdf_buffer, filename, "⬇️ Download PDF"), unsafe_allow_html=True)
                st.success("✅ PDF report generated!")
        
        with col2:
            if st.button("🎨 Create Social Card", use_container_width=True):
                from utils.export_utils import create_social_card, get_download_link
                
                card_buffer = create_social_card(
                    st.session_state.nutrition_data,
                    st.session_state.dish_name or "Food Analysis",
                    st.session_state.image_base64
                )
                
                filename = f"nutrition_card_{st.session_state.dish_name.replace(' ', '_').lower()}.png"
                st.markdown(get_download_link(card_buffer, filename, "⬇️ Download Image"), unsafe_allow_html=True)
                st.image(card_buffer, caption="Social Media Card Preview", use_column_width=True)
                st.success("✅ Social card created!")
        
        with col3:
            if st.button("📋 Copy Analysis", use_container_width=True):
                share_text = f"""🍽️ {st.session_state.dish_name}
                
📊 Nutrition (per 100g):
- Calories: {st.session_state.nutrition_data.get('calories', 'N/A')} kcal
- Protein: {st.session_state.nutrition_data.get('protein', 'N/A')}g
- Carbs: {st.session_state.nutrition_data.get('carbs', 'N/A')}g
- Fat: {st.session_state.nutrition_data.get('fat', 'N/A')}g

🎯 Health Score: {st.session_state.nutrition_data.get('health_score', 'N/A')}/100

Generated by NutriVision AI"""
                
                st.code(share_text, language=None)
                st.info("📋 Copy the text above to share!")
    
    if st.session_state.analyzed:
        for message in st.session_state.messages:
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
        
        prompt = st.chat_input("Ask about this food...")
        
        if prompt:
            st.session_state.messages.append({"role": "user", "content": prompt})
            
            with st.chat_message("user"):
                st.markdown(prompt)
            
            with st.chat_message("assistant"):
                try:
                    api_messages = []
                    
                    if len(st.session_state.messages) == 1:
                        api_messages.append({
                            "role": "user",
                            "content": prompt,
                            "image": st.session_state.image_base64
                        })
                    else:
                        for i, msg in enumerate(st.session_state.messages):
                            if i == 0:
                                api_messages.append({
                                    "role": "user",
                                    "content": msg["content"],
                                    "image": st.session_state.image_base64
                                })
                            else:
                                api_messages.append(msg)
                    
                    if st.session_state.streaming_enabled:
                        response_placeholder = st.empty()
                        full_response = ""
                        start_time = time.time()
                        
                        for chunk in call_qubrid_api_stream(api_messages):
                            full_response += chunk
                            response_placeholder.markdown(full_response + "▌")
                        
                        response_placeholder.markdown(full_response)
                        response = full_response
                        end_time = time.time()
                        
                        response_length = len(response)
                        estimated_tokens = response_length // 4
                        tokens_per_second = estimated_tokens / (end_time - start_time) if (end_time - start_time) > 0 else 0
                        
                        st.markdown(f"""
                        <div style="background: rgba(255,255,255,0.9); border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; border: 1px solid rgba(0,0,0,0.05); display: flex; justify-content: space-around; font-size: 0.8rem; color: #64748b;">
                            <span><strong style="color: #6366f1;">{estimated_tokens}</strong> tokens</span>
                            <span>•</span>
                            <span><strong style="color: #10b981;">{end_time - start_time:.2f}s</strong></span>
                            <span>•</span>
                            <span><strong style="color: #f59e0b;">{tokens_per_second:.1f}</strong> t/s</span>
                        </div>
                        """, unsafe_allow_html=True)
                    else:
                        with st.spinner("Thinking..."):
                            start_time = time.time()
                            response = call_qubrid_api(api_messages)
                            end_time = time.time()
                            st.markdown(response)
                            
                            response_length = len(response)
                            estimated_tokens = response_length // 4
                            tokens_per_second = estimated_tokens / (end_time - start_time) if (end_time - start_time) > 0 else 0
                            
                            st.markdown(f"""
                            <div style="background: rgba(255,255,255,0.9); border-radius: 8px; padding: 0.75rem 1rem; margin: 0.5rem 0; border: 1px solid rgba(0,0,0,0.05); display: flex; justify-content: space-around; font-size: 0.8rem; color: #64748b;">
                                <span><strong style="color: #6366f1;">{estimated_tokens}</strong> tokens</span>
                                <span>•</span>
                                <span><strong style="color: #10b981;">{end_time - start_time:.2f}s</strong></span>
                                <span>•</span>
                                <span><strong style="color: #f59e0b;">{tokens_per_second:.1f}</strong> t/s</span>
                            </div>
                            """, unsafe_allow_html=True)
                    
                    if response:
                        st.session_state.messages.append({"role": "assistant", "content": response})
                    
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")

if not st.session_state.uploaded_image:
    st.markdown("---")
    st.markdown('''
    <div style="text-align: center; padding: 2rem;">
        <p style="color: rgba(255, 255, 255, 0.7); font-size: 0.9rem;">
            NutriVision AI • Powered by Qubrid Vision Model
        </p>
    </div>
    ''', unsafe_allow_html=True)