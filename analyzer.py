import streamlit as st
import re
import random
import datetime
import requests
from googleapiclient.discovery import build
from collections import Counter
import time

# --- 1. CONFIG ---
st.set_page_config(
    page_title="YouTube SEO Pro", 
    page_icon="🎬", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CUSTOM CSS ---
st.markdown("""
<style>
    /* Main Theme */
    .main {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 2rem;}
    .stApp {background: transparent;}
    
    /* Cards */
    .metric-card {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9ff 100%);
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 8px 32px rgba(0,0,0,0.1);
        border: 2px solid rgba(255,255,255,0.3);
        margin: 1rem 0;
    }
    
    /* Score Circle */
    .score-circle {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 2.5rem;
        font-weight: bold;
        margin: 0 auto;
        box-shadow: 0 8px 24px rgba(0,0,0,0.15);
    }
    
    /* Title */
    .app-title {
        text-align: center;
        color: white;
        font-size: 3rem;
        font-weight: 800;
        text-shadow: 2px 2px 8px rgba(0,0,0,0.3);
        margin-bottom: 2rem;
    }
    
    /* Badges */
    .badge {
        display: inline-block;
        padding: 0.4rem 0.8rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.2rem;
    }
    .badge-success {background: #10b981; color: white;}
    .badge-warning {background: #f59e0b; color: white;}
    .badge-error {background: #ef4444; color: white;}
    .badge-info {background: #3b82f6; color: white;}
    
    /* Progress Bar Enhanced */
    .progress-container {
        background: rgba(255,255,255,0.2);
        border-radius: 10px;
        height: 20px;
        overflow: hidden;
        margin: 1rem 0;
    }
    .progress-bar {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
        background: linear-gradient(90deg, #10b981, #3b82f6);
    }
    
    /* Video Card */
    .video-card {
        background: white;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
        box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        transition: transform 0.3s ease;
    }
    .video-card:hover {transform: translateY(-5px); box-shadow: 0 8px 24px rgba(0,0,0,0.15);}
    
    /* Button Enhancement */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 10px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        transition: all 0.3s ease;
    }
    .stButton>button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 24px rgba(102, 126, 234, 0.4);
    }
    
    /* Input Fields */
    .stTextInput>div>div>input {
        border-radius: 10px;
        border: 2px solid #e5e7eb;
        padding: 0.75rem;
    }
    .stTextInput>div>div>input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
</style>
""", unsafe_allow_html=True)

# --- 3. DATABASE CONFIG ---
URL_DATABASE_ONLINE = "https://gist.githubusercontent.com/rhanierex/f2d76f11df8d550376d81b58124d3668/raw/0b58a1eb02a7cffc2261a1c8d353551f3337001c/gistfile1.txt"
FALLBACK_POWER_WORDS = ["secret", "best", "exposed", "tutorial", "guide", "review", "tips", "ultimate", "proven", "insane", "shocking", "amazing", "perfect", "easy", "fast", "free"]
VIRAL_EMOJIS = ["🔥", "😱", "🔴", "✅", "❌", "🎵", "⚠️", "⚡", "🚀", "💰", "💯", "🤯", "😭", "😡", "😴", "🌙", "✨", "💤", "🌧️", "🎹", "🎯", "💎", "🏆", "👑"]
STOP_WORDS = {"the", "and", "or", "for", "to", "in", "on", "at", "by", "with", "a", "an", "is", "it", "of", "that", "this", "video", "how", "what", "why", "when"}

# --- 4. ENHANCED DATA LOADING ---
@st.cache_data(ttl=600)
def load_power_words(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list):
                return data, "🟢 Database Online"
    except:
        pass
    return FALLBACK_POWER_WORDS, "🟠 Using Offline Database"

POWER_WORDS_DB, db_status = load_power_words(URL_DATABASE_ONLINE)

# --- 5. CORE LOGIC (ENHANCED V22) ---

def smart_truncate(text, max_length):
    """Truncate text intelligently at word boundaries"""
    text = text.strip()
    if len(text) <= max_length:
        return text
    truncated = text[:max_length-3].rsplit(' ', 1)[0]
    return truncated + "..."

def clean_title_text(title, keyword):
    """Remove keyword duplicates and clean formatting"""
    if not keyword:
        return title
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    clean = pattern.sub("", title).strip()
    clean = re.sub(r'^[:\-\|]\s*', '', clean)
    clean = re.sub(r'\s+', ' ', clean)
    return clean

def extract_keywords_from_title(title, top_n=5):
    """Extract most important keywords using frequency analysis"""
    words = re.findall(r'\b[a-z]{3,}\b', title.lower())
    filtered = [w for w in words if w not in STOP_WORDS]
    counter = Counter(filtered)
    return [word for word, _ in counter.most_common(top_n)]

def generate_tags(title, keyword, enhanced=True):
    """Generate optimized tags with variations"""
    tags = set()
    year = datetime.datetime.now().year
    
    # Add primary keyword
    tags.add(keyword.lower())
    tags.add(f"{keyword.lower()} {year}")
    
    # Extract from title
    clean_title = re.sub(r'[^\w\s]', '', title.lower())
    words = clean_title.split()
    
    for word in words:
        if word not in STOP_WORDS and len(word) > 2:
            tags.add(word)
    
    if enhanced:
        # Add keyword variations
        kw_words = keyword.lower().split()
        if len(kw_words) > 1:
            tags.add(kw_words[0])
            tags.add(' '.join(kw_words[:2]))
        
        # Add related search terms
        extracted = extract_keywords_from_title(title)
        for kw in extracted[:3]:
            tags.add(kw)
            tags.add(f"{kw} {year}")
    
    return list(tags)[:20]

def generate_description(title, keyword, tags, enhanced=True):
    """Generate SEO-optimized description"""
    year = datetime.datetime.now().year
    month = datetime.datetime.now().strftime("%B")
    
    top_tags = tags[:5]
    hashtags = ' '.join([f"#{tag.replace(' ', '')}" for tag in top_tags])
    
    if enhanced:
        return f"""🎬 **{title}**

📌 **About This Video:**
In this comprehensive guide, we dive deep into **{keyword}**. Whether you're a beginner or advanced, this {year} tutorial will help you master {keyword}.

⏱️ **Timestamps:**
0:00 - Introduction
0:45 - What is {keyword}?
2:30 - Step-by-step {keyword} guide
5:15 - Pro tips and tricks
7:30 - Common mistakes to avoid
9:00 - Conclusion & Next steps

🔥 **Why Watch This?**
✅ Updated for {month} {year}
✅ Practical examples
✅ Expert insights
✅ Proven techniques

💡 **Related Topics:**
{', '.join(top_tags)}

🔔 **Don't Forget to:**
• SUBSCRIBE for more content
• LIKE if this helped you
• COMMENT your questions below
• SHARE with friends

📱 **Follow Us:**
[Add your social media links]

{hashtags}

---
© {year} | {keyword.title()} Guide | All Rights Reserved
"""
    else:
        return f"""🔴 **{title}**

In this video, we explore **{keyword}**. Complete guide for {year}.

👇 **Timestamps:**
0:00 Intro
0:30 {keyword.title()}
5:00 Conclusion

🔔 **SUBSCRIBE!**

#Hashtags:
{hashtags}
"""

def generate_smart_suggestions(original_title, keyword, api_key=None, count=5):
    """Generate multiple title variations with different strategies"""
    suggestions = []
    year = datetime.datetime.now().year
    
    # Get dynamic power word from YouTube API
    power_word = random.choice(POWER_WORDS_DB).upper()
    if api_key:
        try:
            yt = build('youtube', 'v3', developerKey=api_key)
            res = yt.search().list(
                q=keyword, 
                type='video', 
                part='snippet', 
                maxResults=3,
                order='viewCount'
            ).execute()
            
            if 'items' in res and res['items']:
                top_title = res['items'][0]['snippet']['title']
                words = top_title.split()
                for w in words:
                    if w.isupper() and len(w) > 3:
                        power_word = w
                        break
        except:
            pass
    
    core = clean_title_text(original_title, keyword) or "Complete Guide"
    emoji = random.choice(VIRAL_EMOJIS)
    
    # Template 1: Classic SEO
    extra_1 = len(keyword) + len(power_word) + len(str(year)) + len(emoji) + 12
    core_1 = smart_truncate(core, 100 - extra_1)
    suggestions.append(f"{keyword.title()}: {core_1} ({power_word} {year}) {emoji}")
    
    # Template 2: Clickbait Power
    extra_2 = len(keyword) + len(power_word) + len(str(year)) + len(emoji) + 12
    core_2 = smart_truncate(core, 100 - extra_2)
    suggestions.append(f"{emoji} {keyword.upper()} {power_word}: {core_2} [{year}]")
    
    # Template 3: Question Format
    extra_3 = len(keyword) + len(str(year)) + len(emoji) + 15
    core_3 = smart_truncate(core, 100 - extra_3)
    suggestions.append(f"How to {keyword.title()} {emoji} {core_3} ({year} Guide)")
    
    # Template 4: Number Hook
    extra_4 = len(keyword) + len(str(year)) + len(emoji) + 20
    core_4 = smart_truncate(core, 100 - extra_4)
    num = random.choice([5, 7, 10, 15])
    suggestions.append(f"{num} {keyword.title()} Tips {emoji} {core_4} | {year}")
    
    # Template 5: Authority
    extra_5 = len(keyword) + len(power_word) + len(str(year)) + len(emoji) + 18
    core_5 = smart_truncate(core, 100 - extra_5)
    suggestions.append(f"{core_5} - {keyword.title()} {emoji} {power_word} Tutorial {year}")
    
    return suggestions[:count]

def analyze_title(title, keyword=""):
    """Comprehensive title analysis with detailed scoring"""
    score = 0
    checks = []
    recommendations = []
    
    title_len = len(title)
    
    # 1. Length Analysis (25 points)
    if 40 <= title_len <= 60:
        score += 25
        checks.append(("success", f"✅ Perfect Length ({title_len} chars)"))
    elif 30 <= title_len <= 70:
        score += 20
        checks.append(("warning", f"⚠️ Good Length ({title_len} chars)"))
    elif title_len <= 100:
        score += 10
        checks.append(("warning", f"⚠️ Acceptable ({title_len} chars)"))
        recommendations.append("Consider shortening to 40-60 characters for better CTR")
    else:
        checks.append(("error", f"❌ Too Long ({title_len} chars)"))
        recommendations.append("CRITICAL: Shorten to under 100 characters")
    
    # 2. Keyword Analysis (25 points)
    if keyword:
        kw_lower = keyword.lower()
        title_lower = title.lower()
        
        if kw_lower in title_lower:
            position = title_lower.find(kw_lower)
            if position < 10:
                score += 25
                checks.append(("success", "✅ Keyword at Start (SEO Perfect)"))
            elif position < 30:
                score += 20
                checks.append(("success", "✅ Keyword in First Half"))
            else:
                score += 15
                checks.append(("warning", "⚠️ Keyword Present (Move Forward)"))
                recommendations.append("Move keyword closer to the beginning")
        else:
            checks.append(("error", "❌ Keyword Missing"))
            recommendations.append("CRITICAL: Add your target keyword")
    else:
        score += 25
    
    # 3. Power Words (20 points)
    power_found = [pw for pw in POWER_WORDS_DB if pw.lower() in title.lower()]
    if power_found:
        score += 20
        checks.append(("success", f"✅ Power Words: {', '.join(power_found[:2])}"))
    else:
        checks.append(("warning", "⚠️ No Power Words"))
        recommendations.append(f"Add power words like: {', '.join(random.sample(POWER_WORDS_DB, 3))}")
    
    # 4. Numbers (10 points)
    numbers = re.findall(r'\d+', title)
    if numbers:
        score += 10
        checks.append(("success", f"✅ Numbers Present: {', '.join(numbers)}"))
    else:
        checks.append(("info", "ℹ️ Consider Adding Numbers"))
        recommendations.append("Add numbers for higher CTR (e.g., '5 Tips', '2024')")
    
    # 5. Brackets/Parentheses (10 points)
    if re.search(r'[\[\(\]\)]', title):
        score += 10
        checks.append(("success", "✅ Brackets/Parentheses Used"))
    else:
        checks.append(("info", "ℹ️ Add Brackets for Clarity"))
        recommendations.append("Use brackets for additional context [2024 Update]")
    
    # 6. Emoji Usage (10 points)
    emoji_found = [e for e in VIRAL_EMOJIS if e in title]
    if emoji_found:
        score += 10
        checks.append(("success", f"✅ Emoji: {' '.join(emoji_found)}"))
    else:
        checks.append(("info", "ℹ️ Add Emoji for Visibility"))
        recommendations.append(f"Add trending emoji: {' '.join(random.sample(VIRAL_EMOJIS, 3))}")
    
    return min(score, 100), checks, recommendations

# --- 6. UI COMPONENTS ---

def render_score_circle(score):
    """Render animated score circle"""
    if score >= 80:
        color = "#10b981"
        grade = "A+"
    elif score >= 70:
        color = "#3b82f6"
        grade = "A"
    elif score >= 60:
        color = "#f59e0b"
        grade = "B"
    else:
        color = "#ef4444"
        grade = "C"
    
    st.markdown(f"""
    <div class="score-circle" style="background: linear-gradient(135deg, {color} 0%, {color}dd 100%); color: white;">
        {score}
    </div>
    <p style="text-align: center; font-size: 1.2rem; font-weight: bold; margin-top: 0.5rem;">Grade: {grade}</p>
    """, unsafe_allow_html=True)

def render_progress_bar(score):
    """Render enhanced progress bar"""
    if score >= 80:
        color = "linear-gradient(90deg, #10b981, #059669)"
    elif score >= 60:
        color = "linear-gradient(90deg, #f59e0b, #d97706)"
    else:
        color = "linear-gradient(90deg, #ef4444, #dc2626)"
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar" style="width: {score}%; background: {color};"></div>
    </div>
    """, unsafe_allow_html=True)

# --- 7. SIDEBAR ---
with st.sidebar:
    st.markdown("### ⚙️ Settings & Status")
    
    if "Online" in db_status:
        st.success(db_status)
    else:
        st.warning(db_status)
    
    st.divider()
    
    st.markdown("### 🔑 YouTube API")
    api_key = st.text_input("API Key", type="password", help="Enter your YouTube Data API v3 key")
    
    if api_key:
        st.success("🟢 API Connected")
    else:
        st.info("💡 Optional: Add API key for enhanced suggestions")
    
    st.divider()
    
    st.markdown("### 📊 Quick Stats")
    st.metric("Power Words", len(POWER_WORDS_DB))
    st.metric("Viral Emojis", len(VIRAL_EMOJIS))
    
    st.divider()
    
    st.markdown("### 💡 Pro Tips")
    st.caption("✅ Keep titles 40-60 characters")
    st.caption("✅ Put keywords at the start")
    st.caption("✅ Use power words & numbers")
    st.caption("✅ Add emojis for visibility")

# --- 8. MAIN APP ---
st.markdown('<h1 class="app-title">🎬 YouTube SEO Pro</h1>', unsafe_allow_html=True)

tab1, tab2, tab3 = st.tabs(["📝 Title Optimizer", "📊 Channel Audit", "🎯 Bulk Analyzer"])

# --- TAB 1: OPTIMIZER ---
with tab1:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    
    col1, col2 = st.columns([2, 3])
    with col1:
        keyword = st.text_input("🎯 Target Keyword", placeholder="e.g., relaxing jazz music", help="Main keyword for SEO")
    with col2:
        title = st.text_input("✍️ Your Video Title", placeholder="Paste or type your title here...", help="Current or draft title")
    
    col_btn1, col_btn2, col_btn3 = st.columns([1, 1, 2])
    with col_btn1:
        analyze_btn = st.button("🔍 Analyze Title", type="primary", use_container_width=True)
    with col_btn2:
        if title and keyword:
            enhance_btn = st.button("✨ Auto-Enhance", use_container_width=True)
        else:
            enhance_btn = False
    
    st.markdown('</div>', unsafe_allow_html=True)
    
    if analyze_btn or enhance_btn:
        if not keyword or not title:
            st.error("⚠️ Please enter both Keyword and Title")
        else:
            with st.spinner("🔄 Analyzing your title..."):
                time.sleep(0.5)  # UX improvement
                score, checks, recommendations = analyze_title(title, keyword)
            
            st.markdown("---")
            
            # Score Display
            col_score, col_details = st.columns([1, 3])
            
            with col_score:
                render_score_circle(score)
            
            with col_details:
                st.markdown("### 📈 Analysis Results")
                
                if score >= 80:
                    st.success("🎉 Excellent! Your title is highly optimized!")
                elif score >= 60:
                    st.warning("👍 Good title, but there's room for improvement")
                else:
                    st.error("⚠️ Your title needs optimization")
                
                render_progress_bar(score)
            
            # Detailed Checks
            st.markdown("---")
            st.markdown("### 🔍 Detailed Analysis")
            
            cols = st.columns(3)
            for i, (check_type, message) in enumerate(checks):
                with cols[i % 3]:
                    if check_type == "success":
                        st.success(message, icon="✅")
                    elif check_type == "warning":
                        st.warning(message, icon="⚠️")
                    elif check_type == "error":
                        st.error(message, icon="❌")
                    else:
                        st.info(message, icon="ℹ️")
            
            # Recommendations
            if recommendations:
                st.markdown("---")
                st.markdown("### 💡 Actionable Recommendations")
                for rec in recommendations:
                    st.info(f"• {rec}")
            
            # Smart Suggestions
            if score < 100 or enhance_btn:
                st.markdown("---")
                st.markdown("### ✨ AI-Powered Title Suggestions")
                st.caption("These titles are optimized for SEO and CTR (100 character limit)")
                
                with st.spinner("🤖 Generating smart suggestions..."):
                    suggestions = generate_smart_suggestions(title, keyword, api_key, count=5)
                
                for i, suggestion in enumerate(suggestions, 1):
                    col_sug, col_copy = st.columns([5, 1])
                    with col_sug:
                        st.code(suggestion, language='text')
                    with col_copy:
                        st.button("📋", key=f"copy_{i}", help="Click to copy")
            
            # Tags & Description
            st.markdown("---")
            st.markdown("### 🏷️ Complete Metadata Package")
            
            tab_tags, tab_desc = st.tabs(["Tags", "Description"])
            
            gen_tags = generate_tags(title, keyword, enhanced=True)
            gen_desc = generate_description(title, keyword, gen_tags, enhanced=True)
            
            with tab_tags:
                st.caption(f"Generated {len(gen_tags)} optimized tags")
                tags_text = ", ".join(gen_tags)
                st.text_area("📋 Copy Tags:", tags_text, height=150, help="Copy and paste into YouTube")
                st.info(f"💡 Character count: {len(tags_text)}/500")
            
            with tab_desc:
                st.caption("SEO-optimized description with timestamps and hashtags")
                st.text_area("📋 Copy Description:", gen_desc, height=300, help="Copy and paste into YouTube")
                st.info(f"💡 Character count: {len(gen_desc)}/5000")

# --- TAB 2: CHANNEL AUDIT ---
with tab2:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("### 🔍 Channel Intelligence Dashboard")
    
    col_input, col_limit = st.columns([3, 1])
    with col_input:
        channel_input = st.text_input("📺 Channel ID", placeholder="UC_x5XG1OV2P6uZZ5FSM9Ttw", help="Must start with 'UC'")
    with col_limit:
        limit = st.selectbox("Videos", [5, 10, 15, 20, 30], index=1)
    
    scan_btn = st.button("🚀 Scan Channel", type="primary", use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)
    
    if scan_btn:
        if not api_key:
            st.error("⚠️ API Key required for channel analysis")
        elif not channel_input.startswith("UC"):
            st.error("❌ Invalid Channel ID (must start with 'UC')")
        else:
            with st.spinner("🔄 Fetching channel data..."):
                try:
                    yt = build('youtube', 'v3', developerKey=api_key)
                    
                    # Get channel info
                    ch_res = yt.channels().list(
                        id=channel_input, 
                        part='snippet,statistics,contentDetails,brandingSettings'
                    ).execute()
                    
                    if not ch_res.get('items'):
                        st.error("❌ Channel not found")
                        st.stop()
                    
                    ch_info = ch_res['items'][0]
                    stats = ch_info['statistics']
                    snippet = ch_info['snippet']
                    
                    st.markdown("---")
                    
                    # Channel Header
                    col_img, col_info = st.columns([1, 4])
                    
                    with col_img:
                        img_url = snippet['thumbnails'].get('high', snippet['thumbnails'].get('medium'))['url']
                        st.image(img_url, width=150)
                    
                    with col_info:
                        st.markdown(f"## {snippet['title']}")
                        st.caption(snippet.get('description', '')[:200] + "...")
                        
                        m1, m2, m3, m4 = st.columns(4)
                        with m1:
                            st.metric("👥 Subscribers", f"{int(stats.get('subscriberCount', 0)):,}")
                        with m2:
                            st.metric("👁️ Total Views", f"{int(stats['viewCount']):,}")
                        with m3:
                            st.metric("🎬 Videos", f"{int(stats['videoCount']):,}")
                        with m4:
                            avg_views = int(stats['viewCount']) / max(int(stats['videoCount']), 1)
                            st.metric("📊 Avg Views", f"{int(avg_views):,}")
                    
                    st.markdown("---")
                    
                    # Get videos
                    up_id = ch_info['contentDetails']['relatedPlaylists']['uploads']
                    vids = yt.playlistItems().list(
                        playlistId=up_id, 
                        part='snippet', 
                        maxResults=limit
                    ).execute()
                    
                    st.markdown(f"### 📹 Latest {len(vids['items'])} Videos Analysis")
                    
                    # Calculate channel average score
                    all_scores = []
                    
                    for idx, item in enumerate(vids['items'], 1):
                        v_title = item['snippet']['title']
                        v_img = item['snippet']['thumbnails']['default']['url']
                        v_date = item['snippet']['publishedAt'][:10]
                        
                        # Guess keyword from title
                        guess_kw = ' '.join(extract_keywords_from_title(v_title, top_n=1)) or v_title.split()[0]
                        score, checks, recs = analyze_title(v_title, guess_kw)
                        all_scores.append(score)
                        
                        st.markdown('<div class="video-card">', unsafe_allow_html=True)
                        
                        col_thumb, col_content, col_score = st.columns([1, 5, 1])
                        
                        with col_thumb:
                            st.image(v_img, width=120)
                        
                        with col_content:
                            st.markdown(f"**#{idx}. {v_title}**")
                            st.caption(f"📅 Published: {v_date}")
                            
                            if score < 70:
                                with st.expander("🔧 View Optimization Suggestions"):
                                    suggestions = generate_smart_suggestions(v_title, guess_kw, api_key, count=3)
                                    for sug in suggestions:
                                        st.code(sug, language='text')
                            else:
                                st.success("✅ Title is well-optimized", icon="✅")
                        
                        with col_score:
                            color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                            st.markdown(f"""
                            <div style="text-align: center;">
                                <div style="font-size: 2rem; font-weight: bold; color: {color};">{score}</div>
                                <div style="font-size: 0.8rem; color: #666;">Score</div>
                            </div>
                            """, unsafe_allow_html=True)
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                    
                    # Channel Summary
                    if all_scores:
                        st.markdown("---")
                        st.markdown("### 📊 Channel Performance Summary")
                        
                        avg_score = sum(all_scores) / len(all_scores)
                        col1, col2, col3, col4 = st.columns(4)
                        
                        with col1:
                            st.metric("Average Score", f"{avg_score:.1f}/100")
                        with col2:
                            excellent = sum(1 for s in all_scores if s >= 80)
                            st.metric("Excellent Titles", f"{excellent}/{len(all_scores)}")
                        with col3:
                            needs_work = sum(1 for s in all_scores if s < 60)
                            st.metric("Needs Optimization", f"{needs_work}/{len(all_scores)}")
                        with col4:
                            if avg_score >= 80:
                                st.success("🏆 Great Channel!")
                            elif avg_score >= 60:
                                st.warning("👍 Good Channel")
                            else:
                                st.error("⚠️ Needs Work")
                
                except Exception as e:
                    st.error(f"❌ Error: {str(e)}")
                    st.caption("Please check your API key and Channel ID")

# --- TAB 3: BULK ANALYZER ---
with tab3:
    st.markdown('<div class="metric-card">', unsafe_allow_html=True)
    st.markdown("### 📊 Bulk Title Analyzer")
    st.caption("Analyze multiple titles at once")
    
    bulk_input = st.text_area(
        "📝 Paste Your Titles (One per line)", 
        height=200,
        placeholder="Title 1\nTitle 2\nTitle 3\n..."
    )
    
    bulk_keyword = st.text_input("🎯 Common Keyword (Optional)", placeholder="e.g., tutorial")
    
    if st.button("🚀 Analyze All Titles", type="primary", use_container_width=True):
        if bulk_input:
            titles_list = [t.strip() for t in bulk_input.split('\n') if t.strip()]
            
            if titles_list:
                st.markdown("---")
                st.markdown(f"### 📈 Analyzing {len(titles_list)} Titles")
                
                results = []
                
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                for idx, title in enumerate(titles_list):
                    status_text.text(f"Analyzing title {idx+1}/{len(titles_list)}...")
                    progress_bar.progress((idx + 1) / len(titles_list))
                    
                    kw = bulk_keyword or extract_keywords_from_title(title, top_n=1)[0] if extract_keywords_from_title(title, top_n=1) else ""
                    score, checks, recs = analyze_title(title, kw)
                    results.append((title, score, kw))
                
                status_text.empty()
                progress_bar.empty()
                
                # Sort by score
                results.sort(key=lambda x: x[1], reverse=True)
                
                # Summary
                avg_score = sum(s for _, s, _ in results) / len(results)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Average Score", f"{avg_score:.1f}/100")
                with col2:
                    best_score = max(s for _, s, _ in results)
                    st.metric("Best Score", f"{best_score}/100")
                with col3:
                    worst_score = min(s for _, s, _ in results)
                    st.metric("Worst Score", f"{worst_score}/100")
                
                st.markdown("---")
                
                # Results table
                for idx, (title, score, kw) in enumerate(results, 1):
                    col_rank, col_title, col_score, col_action = st.columns([1, 6, 2, 2])
                    
                    with col_rank:
                        st.markdown(f"**#{idx}**")
                    
                    with col_title:
                        st.markdown(f"{title[:80]}{'...' if len(title) > 80 else ''}")
                        if kw:
                            st.caption(f"Keyword: {kw}")
                    
                    with col_score:
                        color = "#10b981" if score >= 80 else "#f59e0b" if score >= 60 else "#ef4444"
                        st.markdown(f'<div style="text-align: center; font-size: 1.5rem; font-weight: bold; color: {color};">{score}</div>', unsafe_allow_html=True)
                    
                    with col_action:
                        if score < 80:
                            if st.button("🔧 Fix", key=f"fix_{idx}"):
                                st.session_state['fix_title'] = title
                                st.session_state['fix_keyword'] = kw
                    
                    st.divider()
            else:
                st.warning("No valid titles found")
        else:
            st.error("Please paste some titles to analyze")
    
    st.markdown('</div>', unsafe_allow_html=True)

# --- FOOTER ---
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: white; padding: 2rem;'>
    <p style='font-size: 0.9rem;'>🎬 <strong>YouTube SEO Pro</strong> | Powered by Sabrani</p>
    <p style='font-size: 0.8rem; opacity: 0.8;'>Optimize your YouTube content for maximum reach and engagement</p>
</div>
""", unsafe_allow_html=True)
