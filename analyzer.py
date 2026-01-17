import streamlit as st
import re
import random
import datetime
import pandas as pd
import requests
import statistics
from googleapiclient.discovery import build

# --- CONFIG ---
st.set_page_config(page_title="YouTube Command Center V12", page_icon="🚀", layout="wide")

# --- DATABASE CONFIG ---
# URL Gist Bapak yang sudah benar
URL_DATABASE_ONLINE = "https://gist.githubusercontent.com/rhanierex/f2d76f11df8d550376d81b58124d3668/raw/0b58a1eb02a7cffc2261a1c8d353551f3337001c/gistfile1.txt"
FALLBACK_POWER_WORDS = ["secret", "best", "exposed", "tutorial", "guide", "review", "tips", "hacks", "fast", "easy"]
VIRAL_EMOJIS = ["🔥", "😱", "🔴", "✅", "❌", "🎵", "⚠️", "⚡", "🚀", "💰", "💯", "🤯", "😭", "😡", "😴", "🌙", "✨", "💤", "🌧️", "🎹"]

# --- LOAD DATA ---
@st.cache_data(ttl=600) 
def load_power_words(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list): return data, "🟢 Online (Gist Active)"
            except: pass
    except: pass
    return FALLBACK_POWER_WORDS, "🟠 Offline (Local DB)"

POWER_WORDS_DB, db_status = load_power_words(URL_DATABASE_ONLINE)

# --- FUNGSI ANALISIS TEKS ---
def clean_title_text(title, keyword):
    if not keyword: return title[:40]
    pattern = re.compile(re.escape(keyword), re.IGNORECASE)
    clean = pattern.sub("", title).strip()
    clean = re.sub(r'^[:\-\|]\s*', '', clean)
    clean = re.sub(r'\[.*?\]', '', clean)
    clean = re.sub(r'\(.*?\)', '', clean)
    return clean[:45].rsplit(' ', 1)[0] + "..." if len(clean) > 45 else clean

def analyze_title(title, keyword=""):
    score = 0
    checks = []
    # 1. Length
    if 20 <= len(title) <= 85: score += 20; checks.append(("success", f"Length OK ({len(title)})"))
    else: checks.append(("warning", f"Length Issue ({len(title)})"))
    # 2. Keyword
    if keyword:
        if keyword.lower() in title.lower():
            score += 15
            clean_kw = re.sub(r'^[^a-zA-Z0-9]+', '', title.lower()).strip()
            if clean_kw.startswith(keyword.lower()):
                score += 15; checks.append(("success", "Keyword Front-Loaded"))
            else: checks.append(("warning", "Keyword Present (Not First)"))
        else: checks.append(("error", "Keyword Missing"))
    else: score += 30
    # 3. Power Words
    if any(pw in title.lower() for pw in POWER_WORDS_DB): score += 20; checks.append(("success", "Power Word Found"))
    else: checks.append(("warning", "No Power Word"))
    # 4. Elements
    if re.search(r'\d+', title): score += 10; checks.append(("success", "Has Number"))
    if re.search(r'[\[\(\]\)]', title): score += 10; checks.append(("success", "Has Brackets"))
    if any(e in title for e in VIRAL_EMOJIS): score += 10; checks.append(("success", "Has Emoji"))
    
    return min(score, 100), checks

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
            if 'items' in res:
                top_title = res['items'][0]['snippet']['title']
                words = top_title.split()
                for w in words:
                    if w.isupper() and len(w) > 3: pwr = w; break
        except: pass

    suggestions.append(f"{keyword.title()}: {core} ({pwr} {year}) {emo}")
    suggestions.append(f"{emo} {keyword.title()} {pwr}: {core} [{year}]")
    return suggestions

# --- FUNGSI DATA INTELLIGENCE (ENGINE V12) ---
def get_keyword_metrics(api_key, keyword):
    if not api_key: return None
    
    youtube = build('youtube', 'v3', developerKey=api_key)
    
    # 1. Search
    search_res = youtube.search().list(q=keyword, type='video', part='id,snippet', maxResults=20, order='relevance').execute()
    video_ids = [item['id']['videoId'] for item in search_res['items']]
    
    if not video_ids: return None
    
    # 2. Stats
    stats_res = youtube.videos().list(id=','.join(video_ids), part='statistics,snippet').execute()
    
    metrics = []
    for item in stats_res['items']:
        views = int(item['statistics'].get('viewCount', 0))
        metrics.append({
            'Title': item['snippet']['title'],
            'Views': views,
            'Channel': item['snippet']['channelTitle'],
            'Date': item['snippet']['publishedAt'][:10]
        })

    df = pd.DataFrame(metrics)
    median_views = statistics.median([m['Views'] for m in metrics])
    
    score = min((median_views / 5000) * 10, 100)
    difficulty = "High" if median_views > 500000 else "Medium" if median_views > 50000 else "Low"
    
    return {'median_views': median_views, 'score': int(score), 'difficulty': difficulty, 'top_videos': df}

# --- UI LAYOUT ---
with st.sidebar:
    st.header("⚙️ Configuration")
    if "Online" in db_status: st.success(db_status)
    else: st.error(db_status)
    st.divider()
    api_key = st.text_input("YouTube API Key", type="password")
    if api_key: st.success("🟢 API Connected")
    else: st.warning("⚪ Offline Mode")

# HEADER
st.title("🚀 YouTube Command Center V12")
st.markdown("Optimization Tool powered by **Data Intelligence**")

# MAIN TABS
tab_research, tab_optimize, tab_audit = st.tabs([
    "🔍 Keyword Inspector (New)", 
    "📝 Title Optimizer", 
    "📺 Channel Audit"
])

# --- TAB 1: KEYWORD INSPECTOR ---
with tab_research:
    st.markdown("### Riset Potensi Kata Kunci")
    kw_input = st.text_input("Masukan Ide Topik/Keyword:", placeholder="Contoh: calming music for cats")
    
    if st.button("Analisa Market"):
        if not api_key:
            st.error("Fitur Riset Market WAJIB menggunakan API Key.")
        elif not kw_input:
            st.warning("Masukan kata kunci dulu.")
        else:
            with st.spinner("Sedang membedah data kompetitor..."):
                try:
                    data = get_keyword_metrics(api_key, kw_input)
                    if data:
                        c1, c2, c3 = st.columns(3)
                        with c1: st.metric("Overall Score", f"{data['score']}/100")
                        with c2: st.metric("Tingkat Kesulitan", data['difficulty'])
                        with c3: st.metric("Median Views", f"{int(data['median_views']):,}")

                        st.divider()
                        st.subheader("📈 Kompetisi di Halaman 1")
                        st.bar_chart(data['top_videos'], x="Title", y="Views")
                        
                        st.subheader("🕵️ Detail Kompetitor")
                        # FIX: Menghapus parameter error 'use_container_width'
                        st.dataframe(data['top_videos'][['Title', 'Channel', 'Views', 'Date']])
                    else:
                        st.error("Gagal mengambil data. Cek API Key atau Kuota.")
                except Exception as e:
                    st.error(f"Terjadi kesalahan: {e}")

# --- TAB 2: TITLE OPTIMIZER ---
with tab_optimize:
    c1, c2 = st.columns([1,2])
    with c1: target_kw = st.text_input("Target Keyword", placeholder="Keyword utama...")
    with c2: draft_title = st.text_input("Draft Judul", placeholder="Judul video anda...")
    
    if st.button("Analisa Judul"):
        if target_kw and draft_title:
            score, logs = analyze_title(draft_title, target_kw)
            
            st.subheader(f"Title Score: {score}/100")
            col_bar = "green" if score >= 80 else "orange" if score >= 60 else "red"
            st.markdown(f"<div style='background-color:#ddd;border-radius:5px'><div style='width:{score}%;background-color:{col_bar};height:10px;border-radius:5px'></div></div>", unsafe_allow_html=True)
            
            if score < 100:
                st.info("💡 **AI Recommendation (100/100):**")
                sugs = generate_smart_suggestions(draft_title, target_kw, api_key)
                for s in sugs: st.code(s, language='text')
            else:
                st.success("Judul sudah sempurna!")
                
            with st.expander("Detail Analisa", expanded=True):
                for stat, msg in logs:
                    if stat == 'success': st.success(msg)
                    elif stat == 'warning': st.warning(msg)
                    elif stat == 'error': st.error(msg)
                    else: st.info(msg)

# --- TAB 3: CHANNEL AUDIT ---
with tab_audit:
    c_id = st.text_input("Channel ID", placeholder="UC...")
    if st.button("Audit Channel"):
        if api_key and c_id:
            with st.spinner("Mengambil data channel..."):
                try:
                    yt = build('youtube', 'v3', developerKey=api_key)
                    ch = yt.channels().list(id=c_id, part='contentDetails').execute()
                    if not ch['items']: st.error("Channel tidak ditemukan."); st.stop()
                    
                    up_id = ch['items'][0]['contentDetails']['relatedPlaylists']['uploads']
                    vids = yt.playlistItems().list(playlistId=up_id, part='snippet', maxResults=10).execute()
                    
                    for item in vids['items']:
                        vt = item['snippet']['title']
                        img = item['snippet']['thumbnails']['default']['url']
                        sc, _ = analyze_title(vt, vt.split()[0] if vt else "Video")
                        
                        with st.container():
                            col_a, col_b = st.columns([1,4])
                            # FIX: Menghapus parameter error 'use_container_width'
                            with col_a: st.image(img) 
                            with col_b:
                                st.write(f"**{vt}**")
                                st.markdown(f"**Score: {sc}**")
                                if sc < 80:
                                    with st.expander("Saran"):
                                        for s in generate_smart_suggestions(vt, vt.split()[0], api_key): st.code(s, language='text')
                            st.divider()
                except Exception as e: st.error(f"Error: {e}")
        else:
            st.error("Butuh API Key & Channel ID")
