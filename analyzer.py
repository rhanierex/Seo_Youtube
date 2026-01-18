import streamlit as st
import re
import random
import datetime
import requests
import statistics
import pandas as pd
from googleapiclient.discovery import build

# --- 1. CONFIG (WAJIB BARIS PERTAMA) ---
st.set_page_config(page_title="YouTube SEO V1", page_icon="🚀", layout="wide")

# --- 2. DATABASE CONFIG ---
URL_DATABASE_ONLINE = "https://gist.githubusercontent.com/rhanierex/f2d76f11df8d550376d81b58124d3668/raw/0b58a1eb02a7cffc2261a1c8d353551f3337001c/gistfile1.txt"
FALLBACK_POWER_WORDS = ["secret", "best", "exposed", "tutorial", "guide"]
VIRAL_EMOJIS = ["🔥", "😱", "🔴", "✅", "❌", "🎵", "⚠️", "⚡", "🚀", "💰", "💯", "🤯", "😭", "😡", "😴", "🌙", "✨", "💤", "🌧️", "🎹"]
STOP_WORDS = ["the", "and", "or", "for", "to", "in", "on", "at", "by", "with", "a", "an", "is", "it", "of", "that", "this", "video"]

# --- 3. LOAD DATA ---
@st.cache_data(ttl=600) 
def load_power_words(url):
    try:
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            try:
                data = response.json()
                if isinstance(data, list) and len(data) > 0: 
                    return data, "🟢 Online"
            except Exception:
                pass
    except Exception:
        pass
    return FALLBACK_POWER_WORDS, "🟠 Offline"

POWER_WORDS_DB, db_status = load_power_words(URL_DATABASE_ONLINE)

# --- 4. CORE LOGIC (Smart Title) ---
def smart_truncate(text, max_length):
    if not text:
        return ""
    text = text.strip()
    if len(text) <= max_length: 
        return text
    truncated = text[:max_length-3]
    last_space = truncated.rfind(' ')
    if last_space > 0:
        truncated = truncated[:last_space]
    return truncated + "..."

def clean_title_text(title, keyword):
    if not keyword or not title: 
        return title
    try:
        pattern = re.compile(re.escape(keyword), re.IGNORECASE)
        clean = pattern.sub("", title).strip()
        clean = re.sub(r'^[:\-\|]\s*', '', clean)
        return clean
    except Exception:
        return title

def generate_tags(title, keyword):
    if not title:
        return [keyword.lower()] if keyword else []
    
    try:
        clean_t = re.sub(r'[^\w\s]', '', title.lower())
        words = clean_t.split()
        tags = [keyword.lower()] if keyword else []
        year = datetime.datetime.now().year
        
        for w in words:
            if w not in STOP_WORDS and w not in tags and len(w) > 2:
                tags.append(w)
                if len(tags) >= 15:
                    break
        
        if keyword:
            tags.append(f"{keyword.lower()} {year}")
        
        return tags[:15]
    except Exception:
        return [keyword.lower()] if keyword else []

def generate_description(title, keyword, tags):
    try:
        year = datetime.datetime.now().year
        tag_text = tags[1] if len(tags) > 1 else 'Viral'
        return f"""🔴 **{title}**

In this video, we explore **{keyword}**. Guide for {year}.

👇 **Timestamps:**
0:00 Intro
0:30 {keyword.title()}
5:00 Conclusion

🔔 **SUBSCRIBE!**

#Hashtags:
#{keyword.replace(" ", "")} #Video #{tag_text}"""
    except Exception:
        return "Video description here."

def generate_smart_suggestions(original_title, keyword, api_key=None):
    suggestions = []
    year = datetime.datetime.now().year
    emo = random.choice(VIRAL_EMOJIS)
    pwr = random.choice(POWER_WORDS_DB).upper()
    
    if api_key and keyword:
        try:
            yt = build('youtube', 'v3', developerKey=api_key)
            res = yt.search().list(
                q=keyword, 
                type='video', 
                part='snippet', 
                maxResults=3
            ).execute()
            
            if 'items' in res and len(res['items']) > 0:
                top_title = res['items'][0]['snippet']['title']
                words = top_title.split()
                for w in words:
                    if w.isupper() and len(w) > 3: 
                        pwr = w
                        break
        except Exception:
            pass

    core = clean_title_text(original_title, keyword) if keyword else original_title
    if not core or core.strip() == "":
        core = "Video"
    
    try:
        # Rumus 1
        extra_1 = len(keyword) + len(pwr) + len(str(year)) + len(emo) + 10 
        sug1 = f"{keyword.title()}: {smart_truncate(core, 100-extra_1)} ({pwr} {year}) {emo}"
        suggestions.append(sug1)

        # Rumus 2
        extra_2 = len(keyword) + len(pwr) + len(str(year)) + len(emo) + 10
        sug2 = f"{emo} {keyword.title()} {pwr}: {smart_truncate(core, 100-extra_2)} [{year}]"
        suggestions.append(sug2)
    except Exception:
        suggestions.append(f"{keyword.title()} - {core} {emo}")
    
    return suggestions

def analyze_title(title, keyword=""):
    score = 0
    checks = []
    
    if not title:
        return 0, [("error", "Title is empty")]
    
    try:
        # Length check
        if 20 <= len(title) <= 60: 
            score += 20
            checks.append(("success", f"Length Perfect ({len(title)})"))
        elif len(title) <= 100: 
            score += 15
            checks.append(("warning", f"Length Good ({len(title)})"))
        else: 
            checks.append(("error", f"Too Long ({len(title)})"))

        # Keyword check
        if keyword:
            if keyword.lower() in title.lower():
                score += 15
                title_start = re.sub(r'^[^a-zA-Z0-9]+', '', title.lower()).strip()
                if title_start.startswith(keyword.lower()):
                    score += 15
                    checks.append(("success", "Keyword First"))
                else: 
                    checks.append(("warning", "Keyword Present"))
            else: 
                checks.append(("error", "Keyword Missing"))
        else: 
            score += 30 

        # Power word check
        if any(pw.lower() in title.lower() for pw in POWER_WORDS_DB): 
            score += 20
            checks.append(("success", "Power Word"))
        else: 
            checks.append(("warning", "No Power Word"))
        
        # Number check
        if re.search(r'\d+', title): 
            score += 10
            checks.append(("success", "Numbers"))
        else: 
            checks.append(("info", "Add Number"))
        
        # Emoji check
        if any(e in title for e in VIRAL_EMOJIS): 
            score += 10
            checks.append(("success", "Emoji"))
        else: 
            checks.append(("info", "Add Emoji"))
        
        return min(score, 100), checks
    except Exception as e:
        return 0, [("error", f"Analysis error: {str(e)}")]

def get_keyword_metrics(api_key, keyword):
    # Validation
    if not api_key or api_key.strip() == "": 
        return None, "❌ API Key kosong. Masukkan API Key di sidebar!"
    
    if len(api_key) < 30:
        return None, "❌ API Key tidak valid. Format: AIzaSy... (39 karakter)"
    
    if not keyword or keyword.strip() == "":
        return None, "❌ Keyword kosong"
    
    try:
        # Build YouTube API with error handling
        try:
            youtube = build('youtube', 'v3', developerKey=api_key)
        except Exception as build_error:
            return None, f"❌ Gagal koneksi ke YouTube API. Periksa API Key Anda. Error: {str(build_error)}"
        
        # Search videos
        try:
            search_res = youtube.search().list(
                q=keyword, 
                type='video', 
                part='id,snippet', 
                maxResults=10, 
                order='relevance',
                regionCode='ID'
            ).execute()
        except Exception as search_error:
            error_msg = str(search_error)
            
            if "API key not valid" in error_msg or "invalid" in error_msg.lower():
                return None, """❌ **API Key TIDAK VALID!**
                
**Kemungkinan masalah:**
1. API Key salah atau typo
2. YouTube Data API v3 belum diaktifkan
3. API Key sudah expired atau dihapus

**Solusi:**
- Periksa ulang API Key di Google Cloud Console
- Pastikan YouTube Data API v3 sudah di-enable
- Buat API Key baru jika perlu
"""
            elif "quota" in error_msg.lower():
                return None, "❌ Quota API habis! Limit: 10,000 units/hari. Coba lagi besok."
            else:
                return None, f"❌ Error saat search: {error_msg}"
        
        # Validate search response
        if not search_res:
            return None, "❌ Tidak ada response dari YouTube API"
            
        if 'items' not in search_res:
            return None, "❌ Format response tidak valid"
            
        if len(search_res['items']) == 0:
            return None, f"❌ Tidak ada video ditemukan untuk keyword: '{keyword}'\n\nCoba keyword yang lebih umum seperti: 'music', 'tutorial', 'gaming'"
        
        # Extract video IDs
        video_ids = []
        for item in search_res['items']:
            try:
                if 'id' in item and 'videoId' in item['id']:
                    video_ids.append(item['id']['videoId'])
            except Exception:
                continue
        
        if not video_ids:
            return None, "❌ Tidak bisa mengambil video ID dari hasil pencarian"
        
        # Get video statistics
        try:
            stats_res = youtube.videos().list(
                id=','.join(video_ids), 
                part='statistics,snippet'
            ).execute()
        except Exception as stats_error:
            return None, f"❌ Error mengambil statistik: {str(stats_error)}"
        
        if not stats_res or 'items' not in stats_res:
            return None, "❌ Gagal mengambil statistik video"
        
        if len(stats_res['items']) == 0:
            return None, "❌ Tidak ada statistik tersedia untuk video yang ditemukan"
        
        # Process metrics
        metrics = []
        for item in stats_res['items']:
            try:
                # Safety checks
                if 'snippet' not in item or 'statistics' not in item:
                    continue
                
                title = item['snippet'].get('title', 'Unknown Title')
                view_count = item['statistics'].get('viewCount', '0')
                channel = item['snippet'].get('channelTitle', 'Unknown')
                published = item['snippet'].get('publishedAt', '2024-01-01T00:00:00Z')
                
                metrics.append({
                    'Title': title,
                    'Views': int(view_count),
                    'Channel': channel,
                    'Date': published[:10]
                })
            except (KeyError, ValueError, TypeError):
                # Skip problematic items
                continue
            
        if not metrics or len(metrics) == 0: 
            return None, "❌ Gagal memproses data video. Tidak ada data valid yang ditemukan."
        
        # Create DataFrame
        df = pd.DataFrame(metrics)
        
        # Calculate metrics
        view_counts = [m['Views'] for m in metrics if m['Views'] > 0]
        
        if not view_counts:
            median_views = 0
            score = 0
            difficulty = "Unknown"
        else:
            median_views = statistics.median(view_counts)
            score = min((median_views / 5000) * 10, 100)
            
            if median_views > 500000:
                difficulty = "🔴 High"
            elif median_views > 50000:
                difficulty = "🟡 Medium"
            else:
                difficulty = "🟢 Low"
        
        result = {
            'median_views': median_views, 
            'score': int(score), 
            'difficulty': difficulty, 
            'top_videos': df
        }
        
        return result, None
        
    except Exception as e:
        return None, f"❌ Error tidak terduga: {str(e)}\n\nTipe: {type(e).__name__}"

# --- 5. VISUALISASI MANUAL (CSS BAR CHART) ---
def draw_safe_chart(df):
    if df is None or df.empty:
        st.warning("No data to display")
        return
    
    try:
        st.markdown("### 📊 Top Competitor Views")
        max_views = df['Views'].max()
        
        if max_views == 0:
            max_views = 1  # Prevent division by zero
        
        for index, row in df.iterrows():
            title = row['Title']
            if len(title) > 40:
                title = title[:40] + "..."
            
            views = row['Views']
            width_pct = int((views / max_views) * 100)
            
            st.markdown(f"""
            <div style="margin-bottom: 10px;">
                <div style="font-size: 14px; font-weight: bold;">{title}</div>
                <div style="font-size: 12px; color: gray;">{row['Channel']} • {views:,} Views</div>
                <div style="background-color: #f0f2f6; width: 100%; height: 10px; border-radius: 5px;">
                    <div style="background-color: #ff4b4b; width: {width_pct}%; height: 10px; border-radius: 5px;"></div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error displaying chart: {str(e)}")

# --- 6. UI UTAMA ---
with st.sidebar:
    st.header("⚙️ Settings")
    if "Online" in db_status: 
        st.success(db_status)
    else: 
        st.warning(db_status)
    st.divider()
    
    st.markdown("### 🔑 YouTube API Key")
    api_key = st.text_input("Masukkan API Key:", type="password", placeholder="AIzaSy...")
    
    if api_key and len(api_key) > 30: 
        st.success("🟢 API Key Terdeteksi")
    elif api_key:
        st.warning("⚠️ API Key terlalu pendek")
    
    with st.expander("📖 Cara Mendapatkan API Key"):
        st.markdown("""
        **Langkah-langkah:**
        
        1. **Buka Google Cloud Console:**
           - [console.cloud.google.com](https://console.cloud.google.com)
        
        2. **Buat Project Baru:**
           - Klik "Select Project" → "New Project"
           - Beri nama project (contoh: "YouTube Tool")
        
        3. **Aktifkan YouTube Data API v3:**
           - Menu ☰ → "APIs & Services" → "Library"
           - Cari "YouTube Data API v3"
           - Klik "Enable"
        
        4. **Buat Credentials:**
           - "APIs & Services" → "Credentials"
           - "Create Credentials" → "API Key"
           - Copy API Key yang muncul
        
        5. **Paste di form di atas ↑**
        
        ⚠️ **Penting:** 
        - API Key gratis (10,000 quota/hari)
        - Jangan share API Key ke orang lain
        - Format: AIzaSy... (39 karakter)
        """)

st.title("🛡️ YouTube SEO V1")

tab1, tab2, tab3 = st.tabs(["🔍 Keyword Inspector", "📝 Video Optimizer", "📺 Channel Audit"])

# TAB 1: KEYWORD
with tab1:
    st.markdown("### 🔍 Analisa Keyword YouTube")
    st.markdown("Masukkan kata kunci untuk melihat potensi dan kompetisi di YouTube")
    
    kw_input = st.text_input("Masukan Topik:", placeholder="Contoh: kucing lucu", key="keyword_input")
    
    if st.button("Analisa Market", type="primary"):
        if not api_key or api_key.strip() == "": 
            st.error("⚠️ Masukkan API Key di sidebar terlebih dahulu!")
            st.info("💡 Cara mendapatkan API Key: https://console.cloud.google.com/apis/credentials")
        elif not kw_input or kw_input.strip() == "": 
            st.warning("⚠️ Masukkan kata kunci terlebih dahulu!")
        else:
            with st.spinner(f"🔎 Menganalisa keyword '{kw_input}'..."):
                try:
                    data, err = get_keyword_metrics(api_key, kw_input)
                    
                    if err: 
                        st.error(err)
                        
                        # Tambahkan troubleshooting tips
                        with st.expander("🛠️ Troubleshooting"):
                            st.markdown("""
                            **Kemungkinan masalah:**
                            1. API Key salah atau expired
                            2. YouTube Data API v3 belum diaktifkan
                            3. Quota API habis (limit: 10,000 units/hari)
                            4. Keyword terlalu spesifik (tidak ada hasil)
                            
                            **Solusi:**
                            - Periksa API Key di Google Cloud Console
                            - Aktifkan YouTube Data API v3
                            - Gunakan keyword yang lebih umum
                            """)
                    
                    elif data and data.get('top_videos') is not None:
                        st.success(f"✅ Berhasil menganalisa '{kw_input}'")
                        
                        # Metrics
                        c1, c2, c3 = st.columns(3)
                        with c1: 
                            st.metric("📊 Potensi Score", f"{data['score']}/100")
                        with c2: 
                            st.metric("🎯 Kesulitan", data['difficulty'])
                        with c3: 
                            st.metric("👁️ Median Views", f"{int(data['median_views']):,}")
                        
                        st.divider()
                        
                        # Chart
                        if not data['top_videos'].empty:
                            draw_safe_chart(data['top_videos'])
                            
                            st.divider()
                            st.markdown("### 📋 Detail Data Kompetitor")
                            
                            # Display table
                            display_df = data['top_videos'][['Title', 'Views', 'Channel', 'Date']].copy()
                            display_df['Views'] = display_df['Views'].apply(lambda x: f"{x:,}")
                            st.dataframe(display_df, use_container_width=True, hide_index=True)
                        else:
                            st.warning("Tidak ada data untuk ditampilkan")
                    else:
                        st.error("❌ Terjadi kesalahan yang tidak diketahui")
                        
                except Exception as e:
                    st.error(f"❌ Error tidak terduga: {str(e)}")
                    st.code(f"Debug info: {type(e).__name__}", language="text")

# TAB 2: OPTIMIZER
with tab2:
    c1, c2 = st.columns([1, 2])
    with c1: 
        keyword = st.text_input("Target Keyword", placeholder="e.g. relaxing jazz")
    with c2: 
        title = st.text_input("Draft Title", placeholder="Paste title here...")
    
    if st.button("Analyze Title"):
        if not title:
            st.warning("Masukkan title terlebih dahulu")
        else:
            score, logs = analyze_title(title, keyword)
            
            # Score Manual CSS
            if score >= 80:
                clr = "#28a745"
            elif score >= 60:
                clr = "#ffc107"
            else:
                clr = "#dc3545"
            
            st.markdown(f"<h1 style='color:{clr}; font-size: 50px;'>{score}/100</h1>", unsafe_allow_html=True)
            st.markdown(f"<div style='background-color:#eee;height:10px;border-radius:5px'><div style='width:{score}%;background-color:{clr};height:10px;border-radius:5px'></div></div>", unsafe_allow_html=True)

            with st.expander("🔍 Detail", expanded=True):
                for s, m in logs:
                    if s == "success": 
                        st.success(m, icon="✅")
                    elif s == "warning": 
                        st.warning(m, icon="⚠️")
                    elif s == "info":
                        st.info(m, icon="ℹ️")
                    else: 
                        st.error(m, icon="❌")

            st.divider()
            if score < 100 and keyword:
                st.info("💡 **Rekomendasi (Smart Fit):**")
                sugs = generate_smart_suggestions(title, keyword, api_key)
                for s in sugs: 
                    st.code(s, language='text')

            st.divider()
            c_tag, c_desc = st.columns(2)
            gen_tags = generate_tags(title, keyword)
            with c_tag: 
                st.text_area("Tags:", ", ".join(gen_tags), height=150)
            with c_desc: 
                st.text_area("Description:", generate_description(title, keyword, gen_tags), height=150)

# TAB 3: AUDIT
with tab3:
    cid = st.text_input("Channel ID (UC...)", placeholder="Contoh: UC_x5XG...")
    if st.button("Scan Channel"):
        if not api_key: 
            st.error("API Key diperlukan")
        elif not cid or not cid.startswith("UC"): 
            st.error("Masukkan Channel ID yang valid (dimulai dengan UC)")
        else:
            with st.spinner("Scanning..."):
                try:
                    yt = build('youtube', 'v3', developerKey=api_key)
                    ch_res = yt.channels().list(
                        id=cid, 
                        part='snippet,statistics,contentDetails'
                    ).execute()
                    
                    if not ch_res.get('items'): 
                        st.error("Channel not found")
                    else:
                        ch = ch_res['items'][0]
                        snip = ch['snippet']
                        stats = ch['statistics']
                        
                        st.markdown("---")
                        col_img, col_txt = st.columns([1, 4])
                        
                        with col_img: 
                            st.image(snip['thumbnails']['medium']['url'], width=100)
                        with col_txt:
                            st.markdown(f"### {snip['title']}")
                            st.markdown(f"**Subs:** {int(stats.get('subscriberCount', 0)):,} | **Views:** {int(stats.get('viewCount', 0)):,}")
                        
                        st.markdown("---")
                        
                        up_id = ch['contentDetails']['relatedPlaylists']['uploads']
                        vids = yt.playlistItems().list(
                            playlistId=up_id, 
                            part='snippet', 
                            maxResults=5
                        ).execute()
                        
                        for item in vids.get('items', []):
                            vt = item['snippet']['title']
                            img = item['snippet']['thumbnails']['default']['url']
                            kw = vt.split()[0] if vt else "Video"
                            sc, _ = analyze_title(vt, kw)
                            
                            with st.container():
                                ca, cb = st.columns([1, 4])
                                with ca: 
                                    st.image(img, width=120)
                                with cb:
                                    st.write(f"**{vt}**")
                                    clr = "green" if sc >= 80 else "red"
                                    st.markdown(f"Score: <span style='color:{clr};font-weight:bold'>{sc}</span>", unsafe_allow_html=True)
                                    if sc < 80:
                                        with st.expander("Fix"):
                                            for s in generate_smart_suggestions(vt, kw, api_key): 
                                                st.code(s, language='text')
                                st.divider()

                except Exception as e: 
                    st.error(f"Error: {str(e)}")
