import streamlit as st
import re
import random
import datetime
import requests
from googleapiclient.discovery import build

# --- 1. CONFIG (WAJIB BARIS PERTAMA) ---
st.set_page_config(page_title="YouTube Master V20", page_icon="✨", layout="wide")

# --- 2. DATABASE CONFIG ---
URL_DATABASE_ONLINE = "https://gist.githubusercontent.com/rhanierex/f2d76f11df8d550376d81b58124d3668/raw/0b58a1eb02a7cffc2261a1c8d353551f3337001c/gistfile1.txt"
FALLBACK_POWER_WORDS = ["secret", "best", "exposed", "tutorial", "guide", "review", "tips"]
VIRAL_EMOJIS = ["🔥", "😱", "🔴", "✅", "❌", "🎵", "⚠️", "⚡", "🚀", "💰", "💯", "🤯", "😭", "😡", "😴", "🌙", "✨", "💤", "🌧️", "🎹"]
STOP_WORDS = ["the", "and", "or", "for", "to", "in", "on", "at", "by", "with", "a", "an", "is", "it", "of", "that", "this", "video"]

# --- 3. LOAD DATA ---
@st.cache_data(ttl=600) 
def load_power_words(url):
    try:
        response = requests.get(url, timeout=3)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list): return data, "🟢 Online"
            except: pass
    except: pass
    return FALLBACK_POWER_WORDS, "🟠 Offline"

POWER_WORDS_DB, db_status = load_power_words(URL_DATABASE_ONLINE)

# --- 4. CORE LOGIC ---
def clean_title_text(title, keyword):
    if not keyword: return title[:40]
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    clean = pattern.sub("", title).strip()
    return clean[:45].rsplit(' ', 1)[0] + "..." if len(clean) > 45 else clean

def generate_tags(title, keyword):
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
    year = datetime.datetime.now().year
    return f"""🔴 **{title}**\n\nIn this video, we explore **{keyword}**. Guide for {year}.\n\n👇 **Timestamps:**\n0:00 Intro\n0:30 {keyword.title()}\n5:00 Conclusion\n\n🔔 **SUBSCRIBE!**\n\n#Hashtags:\n#{keyword.replace(" ", "")} #Video #{tags[1] if len(tags)>1 else 'Viral'}"""

def generate_smart_suggestions(original_title, keyword, api_key=None):
    suggestions = []
    core = clean_title_text(original_title, keyword) or "Video"
    year = datetime.datetime.now().year
    emo = random.choice(VIRAL_EMOJIS)
    pwr = random.choice(POWER_WORDS_DB).upper()
    
    if api_key:
        try:
            yt = build('youtube', 'v3', developerKey=api_key)
            res = yt.search().list(q=keyword, type='video', part='snippet', maxResults=3).execute()
            if 'items' in res and res['items']:
                top_title = res['items'][0]['snippet']['title']
                words = top_title.split()
                for w in words:
                    if w.isupper() and len(w) > 3: pwr = w; break
        except: pass

    suggestions.append(f"{keyword.title()}: {core} ({pwr} {year}) {emo}")
    suggestions.append(f"{emo} {keyword.title()} {pwr}: {core} [{year}]")
    suggestions.append(f"{core} - {keyword.title()} {emo} ({pwr} {year})")
    return suggestions

def analyze_title(title, keyword=""):
    score = 0
    checks = []
    
    if 20 <= len(title) <= 85: score += 20; checks.append(("success", f"Length ({len(title)})"))
    else: checks.append(("warning", f"Length ({len(title)})"))

    if keyword:
        if keyword.lower() in title.lower():
            score += 15
            clean_start = re.sub(r'^[^a-zA-Z0-9]+', '', title.lower()).strip()
            if clean_start.startswith(keyword.lower()): score += 15; checks.append(("success", "Keyword First"))
            else: checks.append(("warning", "Keyword Present"))
        else: checks.append(("error", "Keyword Missing"))
    else: score += 30 

    if any(pw in title.lower() for pw in POWER_WORDS_DB): score += 20; checks.append(("success", "Power Word"))
    else: checks.append(("warning", "No Power Word"))

    if re.search(r'\d+', title): score += 10; checks.append(("success", "Numbers"))
    else: checks.append(("info", "Add Number"))
    if re.search(r'[\[\(\]\)]', title): score += 10; checks.append(("success", "Brackets"))
    else: checks.append(("info", "Add Brackets"))
    if any(e in title for e in VIRAL_EMOJIS): score += 10; checks.append(("success", "Emoji"))
    
    return min(score, 100), checks

# --- 5. UI LAYOUT ---
with st.sidebar:
    st.header("⚙️ Settings")
    if "Online" in db_status: st.success(db_status)
    else: st.warning(db_status)
    st.divider()
    st.header("🔑 API Key")
    api_key = st.text_input("Paste YouTube API Key Here", type="password")
    if api_key: st.success("🟢 API Connected")
    else: st.warning("⚪ Disconnected")

st.title("✨ YouTube Master V20")

tab1, tab2 = st.tabs(["📝 Video Optimizer", "📊 Channel Intelligence"])

# --- TAB 1: OPTIMIZER ---
with tab1:
    c1, c2 = st.columns([1, 2])
    with c1: keyword = st.text_input("Target Keyword", placeholder="e.g. relaxing jazz")
    with c2: title = st.text_input("Draft Title", placeholder="Paste title here...")
        
    if st.button("Analyze Title", type="primary"):
        if keyword and title:
            score, logs = analyze_title(title, keyword)
            
            # Score
            col_score, col_text = st.columns([1, 4])
            with col_score:
                color = "green" if score >= 80 else "orange" if score >= 60 else "red"
                st.markdown(f"<h1 style='color:{color}; font-size: 50px; margin:0;'>{score}</h1>", unsafe_allow_html=True)
            with col_text:
                if score >= 80: st.success("Excellent Title!")
                elif score >= 60: st.warning("Good, but needs optimization.")
                else: st.error("Needs improvement.")
            
            st.markdown(f"<div style='background-color:#555;height:8px;border-radius:4px;margin-bottom:20px'><div style='width:{score}%;background-color:{color};height:8px;border-radius:4px'></div></div>", unsafe_allow_html=True)

            # Details
            with st.expander("🔍 Lihat Detail Analisa", expanded=True):
                cols = st.columns(3)
                for i, (type_log, msg) in enumerate(logs):
                    with cols[i % 3]:
                        if type_log == "success": st.success(msg, icon="✅")
                        elif type_log == "warning": st.warning(msg, icon="⚠️")
                        elif type_log == "error": st.error(msg, icon="❌")
                        else: st.info(msg, icon="ℹ️")

            st.divider()
            
            # Recommendations
            if score < 100:
                st.info("💡 **Rekomendasi Judul (Skor 100):**")
                sugs = generate_smart_suggestions(title, keyword, api_key)
                for s in sugs: st.code(s, language='text')

            # Tags & Desc
            st.divider()
            c_tag, c_desc = st.columns(2)
            gen_tags = generate_tags(title, keyword)
            
            with c_tag:
                st.subheader("🏷️ Tags")
                st.text_area("Copy Tags:", ", ".join(gen_tags), height=150)
            with c_desc:
                st.subheader("📝 Description")
                st.text_area("Copy Description:", generate_description(title, keyword, gen_tags), height=150)
        else:
            st.error("Mohon isi Keyword dan Judul.")

# --- TAB 2: CHANNEL AUDIT (FIXED UI) ---
with tab2:
    st.markdown("### 📥 Channel Intelligence")
    c_a1, c_a2 = st.columns([3, 1])
    with c_a1: channel_input = st.text_input("Channel ID (Harus 'UC...')", placeholder="Contoh: UC_x5XG...")
    with c_a2: limit = st.selectbox("Max Video", [5, 10, 20], index=1)
        
    if st.button("🔍 Scan Channel", type="primary"):
        if not api_key: st.error("Wajib pakai API Key.")
        elif not channel_input.startswith("UC"): st.error("Format Channel ID salah (Harus UC...).")
        else:
            with st.spinner("Mengambil data channel..."):
                try:
                    yt = build('youtube', 'v3', developerKey=api_key)
                    
                    # 1. GET CHANNEL STATS
                    ch_res = yt.channels().list(id=channel_input, part='snippet,statistics,contentDetails').execute()
                    if not ch_res['items']: st.error("Channel tidak ditemukan."); st.stop()
                    
                    ch_info = ch_res['items'][0]
                    stats = ch_info['statistics']
                    snippet = ch_info['snippet']
                    
                    # 2. UI DASHBOARD (FIXED)
                    st.markdown("---")
                    
                    # Layout Kolom
                    col_profile, col_metrics = st.columns([1, 4])
                    
                    with col_profile:
                        # Menggunakan gambar 'high' resolution agar tidak pecah/broken
                        img_url = snippet['thumbnails'].get('high', snippet['thumbnails'].get('medium'))['url']
                        st.image(img_url, width=150)
                        st.markdown(f"**{snippet['title']}**")
                    
                    with col_metrics:
                        # Menggunakan st.metric standar (Aman untuk Dark/Light Mode)
                        m1, m2, m3 = st.columns(3)
                        with m1: st.metric("Subscribers", f"{int(stats['subscriberCount']):,}")
                        with m2: st.metric("Total Views", f"{int(stats['viewCount']):,}")
                        with m3: st.metric("Total Videos", f"{int(stats['videoCount']):,}")

                    st.markdown("---")

                    # 3. GET VIDEOS
                    up_id = ch_info['contentDetails']['relatedPlaylists']['uploads']
                    vids = yt.playlistItems().list(playlistId=up_id, part='snippet', maxResults=limit).execute()
                    
                    st.subheader(f"Analisa {len(vids['items'])} Video Terakhir")
                    
                    for item in vids['items']:
                        v_title = item['snippet']['title']
                        v_img = item['snippet']['thumbnails']['default']['url']
                        guess_kw = v_title.split()[0] if v_title else "Video"
                        score, _ = analyze_title(v_title, guess_kw)
                        
                        # Layout Card
                        with st.container():
                            c_img, c_body, c_score = st.columns([1, 4, 1])
                            with c_img: st.image(v_img, width=150)
                            with c_body:
                                st.write(f"**{v_title}**")
                                if score < 80:
                                    with st.expander("🔧 Perbaikan Judul"):
                                        sugs = generate_smart_suggestions(v_title, guess_kw, api_key)
                                        for s in sugs: st.code(s, language='text')
                                else:
                                    st.caption("✅ Judul sudah optimal.")
                            with c_score:
                                color = "green" if score >= 80 else "red"
                                st.markdown(f"<h2 style='text-align:center; color:{color};'>{score}</h2>", unsafe_allow_html=True)
                            st.divider()

                except Exception as e:
                    st.error(f"Error: {e}")
