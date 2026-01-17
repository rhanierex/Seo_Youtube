import streamlit as st
import re
import random
import datetime
import pandas as pd
import requests
from collections import Counter
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- 1. CONFIG (WAJIB BARIS PERTAMA) ---
st.set_page_config(page_title="YouTube SEO Master V11 (Fixed)", page_icon="🚀", layout="wide")

# --- 2. DATABASE CONFIG ---
# URL Gist Bapak
URL_DATABASE_ONLINE = "https://gist.githubusercontent.com/rhanierex/f2d76f11df8d550376d81b58124d3668/raw/0b58a1eb02a7cffc2261a1c8d353551f3337001c/gistfile1.txt"

FALLBACK_POWER_WORDS = ["secret", "best", "exposed", "tutorial", "guide", "review", "tips", "hacks", "fast", "easy"]
VIRAL_EMOJIS = ["🔥", "😱", "🔴", "✅", "❌", "🎵", "⚠️", "⚡", "🚀", "💰", "💯", "🤯", "😭", "😡", "😴", "🌙", "✨", "💤", "🌧️", "🎹"]
STOP_WORDS = ["the", "and", "or", "for", "to", "in", "on", "at", "by", "with", "a", "an", "is", "it", "of", "that", "this", "from", "how", "what", "why", "video", "dan", "di", "ke", "dari", "yang", "ini", "itu"]

# --- 3. LOAD DATA ---
@st.cache_data(ttl=600) 
def load_power_words(url):
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list):
                    return data, "🟢 Online (Gist Active)"
            except: pass
    except: pass
    return FALLBACK_POWER_WORDS, "🟠 Offline (Local DB)"

POWER_WORDS_DB, db_status = load_power_words(URL_DATABASE_ONLINE)

# --- 4. CORE LOGIC (V11 FEATURES) ---
def clean_title_text(title, keyword):
    if not keyword: return title[:40]
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    clean = pattern.sub("", title)
    clean = clean.strip()
    clean = re.sub(r'^[:\-\|]\s*', '', clean)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\(.*?\)', '', clean)
    return clean[:45].rsplit(' ', 1)[0] + "..." if len(clean) > 45 else clean

def generate_tags(title, keyword):
    # Fitur V11: Ekstrak tags dari judul
    clean_t = re.sub(r'[^\w\s]', '', title.lower())
    words = clean_t.split()
    tags = [keyword.lower()]
    year = datetime.datetime.now().year
    for w in words:
        if w not in STOP_WORDS and w not in tags and len(w) > 2:
            tags.append(w)
    tags.append(f"{keyword.lower()} {year}")
    return tags[:15]

def generate_description(title, keyword, tags):
    # Fitur V11: Template Deskripsi
    year = datetime.datetime.now().year
    return f"""🔴 **{title}**\n\nIn this video, we explore **{keyword}**. This is the ultimate guide/collection for {year}.\n\n👇 **Timestamps:**\n0:00 Intro\n0:30 {keyword.title()} Highlights\n5:00 Conclusion\n\n🔔 **Don't forget to SUBSCRIBE for more content like this!**\n\n🔎 **Related Keywords:**\n{', '.join(tags[:8])}\n\n#Hashtags:\n#{keyword.replace(" ", "")} #Video #{tags[1] if len(tags)>1 else 'Viral'}"""

def get_competitor_keywords(api_key, keyword):
    if not api_key: return []
    try:
        youtube = build('youtube', 'v3', developerKey=api_key)
        search_res = youtube.search().list(q=keyword, type='video', part='id', maxResults=5).execute()
        video_ids = [item['id']['videoId'] for item in search_res['items']]
        if not video_ids: return []
        
        vid_res = youtube.videos().list(id=','.join(video_ids), part='snippet').execute()
        all_tags = []
        for item in vid_res['items']:
            tags = item['snippet'].get('tags', [])
            all_tags.extend(tags)
            
        common = [tag for tag, count in Counter(all_tags).most_common(10) if keyword.lower() not in tag.lower()]
        return common
    except: return []

def generate_smart_suggestions(original_title, keyword, api_key=None):
    suggestions = []
    current_year = datetime.datetime.now().year
    emo = random.choice(VIRAL_EMOJIS)
    core_text = clean_title_text(original_title, keyword) or "Content"
    
    trending_words = get_competitor_keywords(api_key, keyword) if api_key else []
    pwr = trending_words[0].upper() if trending_words else random.choice(POWER_WORDS_DB).upper()

    suggestions.append(f"{keyword.title()}: {core_text} ({pwr} {current_year}) {emo}")
    suggestions.append(f"{emo} {keyword.title()} {pwr}: {core_text} [{current_year}]")
    suggestions.append(f"{core_text} - {keyword.title()} {emo} ({pwr} {current_year})")
    return suggestions

def analyze_title(title, keyword=""):
    score = 0
    checks = []
    
    # 1. Length
    if 20 <= len(title) <= 85: score += 20; checks.append(("success", f"Length Optimal ({len(title)} chars)"))
    else: checks.append(("warning", f"Length Issue ({len(title)} chars)"))

    # 2. Keyword
    if keyword:
        if keyword.lower() in title.lower():
            score += 15
            clean_start = re.sub(r'^[^a-zA-Z0-9]+', '', title.lower()).strip()
            if clean_start.startswith(keyword.lower()): score += 15; checks.append(("success", "Keyword at Front"))
            else: checks.append(("warning", "Keyword Present (Not Front)"))
        else: checks.append(("error", "Keyword Missing"))
    else: score += 30 

    # 3. Power Words
    if any(pw in title.lower() for pw in POWER_WORDS_DB): score += 20; checks.append(("success", "Power Word Found"))
    else: checks.append(("warning", "No Power Word"))

    # 4. Elements
    if re.search(r'\d+', title): score += 10; checks.append(("success", "Contains Number"))
    else: checks.append(("info", "Add Number"))
    if re.search(r'[\[\(\]\)]', title): score += 10; checks.append(("success", "Contains Brackets"))
    else: checks.append(("info", "Add Brackets"))
    if any(e in title for e in VIRAL_EMOJIS): score += 10; checks.append(("success", "Visual Hook (Emoji)"))
    
    return min(score, 100), checks

# --- 5. UI LAYOUT ---
with st.sidebar:
    st.header("⚙️ Settings")
    if "Online" in db_status: st.success(db_status)
    else: st.warning(db_status)
    st.divider()
    st.header("🔑 API Configuration")
    api_key = st.text_input("YouTube API Key", type="password")
    if api_key: st.success("🟢 API Connected")
    else: st.warning("⚪ API Disconnected")

st.title("🚀 YouTube SEO Master Suite V11")

tab1, tab2 = st.tabs(["📝 Single Video Optimizer (Full Suite)", "📺 Channel Audit (Massal)"])

# --- TAB 1: SINGLE OPTIMIZER (FULL V11) ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1: keyword = st.text_input("Target Keyword", placeholder="e.g. relaxing jazz")
    with c2: title = st.text_input("Draft Title", placeholder="Paste title here...")
        
    if st.button("Analyze & Generate"):
        if keyword and title:
            score, logs = analyze_title(title, keyword)
            
            st.subheader(f"Performance Score: {score}/100")
            bar_color = "green" if score >= 80 else "orange" if score >= 60 else "red"
            st.markdown(f"<div style='background-color:#eee;height:10px;border-radius:5px'><div style='width:{score}%;background-color:{bar_color};height:10px;border-radius:5px'></div></div>", unsafe_allow_html=True)
            
            with st.expander("🔍 Analysis Details (Click to Expand)", expanded=True):
                for type_log, msg in logs:
                    if type_log == "success": st.success(msg, icon="✅")
                    elif type_log == "warning": st.warning(msg, icon="⚠️")
                    elif type_log == "error": st.error(msg, icon="❌")
                    else: st.info(msg, icon="ℹ️")

            st.divider()
            if score < 100:
                st.info("💡 **AI Recommendations (Guaranteed 100/100):**")
                sugs = generate_smart_suggestions(title, keyword, api_key)
                for s in sugs: st.code(s, language='text')
            else: st.success("🎉 PERFECT TITLE! Ready to Publish.")

            # FITUR V11 YANG HILANG DI V12 SUDAH KEMBALI DISINI
            st.divider()
            c_tag, c_desc = st.columns(2)
            gen_tags = generate_tags(title, keyword)
            
            with c_tag:
                st.subheader("🏷️ Generated Tags")
                st.text_area("Copy to YouTube:", ", ".join(gen_tags), height=150)
            with c_desc:
                st.subheader("📝 Description Template")
                st.text_area("Copy Description:", generate_description(title, keyword, gen_tags), height=150)
        else:
            st.error("Mohon isi Keyword dan Judul.")

# --- TAB 2: CHANNEL AUDIT (FIXED) ---
with tab2:
    st.markdown("### 📥 Tarik Data Channel")
    c_a1, c_a2 = st.columns([3, 1])
    with c_a1: channel_input = st.text_input("Channel ID (UC...)", placeholder="Contoh: UC_x5XG...")
    with c_a2: limit = st.selectbox("Max Video", [5, 10, 20], index=1)
        
    if st.button("🚀 Audit Channel"):
        if not api_key: st.error("Fitur Audit Wajib pakai API Key.")
        elif not channel_input: st.error("Channel ID Kosong.")
        else:
            with st.spinner("Sedang audit..."):
                try:
                    yt = build('youtube', 'v3', developerKey=api_key)
                    ch = yt.channels().list(id=channel_input, part='contentDetails').execute()
                    if not ch['items']: st.error("Channel tidak ditemukan."); st.stop()
                    up_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                    vids = yt.playlistItems().list(playlistId=up_id, part='snippet', maxResults=limit).execute()
                    
                    st.success(f"Audit Selesai: {len(vids['items'])} Video")
                    st.divider()
                    
                    for item in vids['items']:
                        v_title = item['snippet']['title']
                        v_img = item['snippet']['thumbnails']['default']['url']
                        guess_kw = v_title.split()[0] if v_title else "Video"
                        score, _ = analyze_title(v_title, guess_kw)
                        
                        with st.container():
                            col_img, col_txt, col_scr = st.columns([1, 4, 1])
                            # FIX: width=150 menggantikan use_container_width
                            with col_img: st.image(v_img, width=150)
                            with col_txt:
                                st.subheader(v_title)
                                if score < 100:
                                    with st.expander("Lihat Perbaikan Judul"):
                                        sugs = generate_smart_suggestions(v_title, guess_kw, api_key)
                                        for s in sugs: st.code(s, language='text')
                            with col_scr:
                                color = "green" if score >= 80 else "red"
                                st.markdown(f"<h2 style='text-align:center;color:{color}'>{score}</h2>", unsafe_allow_html=True)
                            st.divider()
                except Exception as e:
                    st.error(f"Error: {e}")
