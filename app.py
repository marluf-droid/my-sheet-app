import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(page_title="Performance Analytics Pro", layout="wide")

# আধুনিক ক্লিন CSS ডিজাইন
st.markdown("""
    <style>
    .metric-card { 
        padding: 15px; border-radius: 12px; text-align: center; color: #1e293b; 
        background: #ffffff; border-top: 5px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
    .rework-border { border-top-color: #ef4444; background-color: #fff1f0; }
    .fp-border { border-top-color: #3b82f6; background-color: #e6f7ff; }
    .mrp-border { border-top-color: #10b981; background-color: #f6ffed; }
    .cad-border { border-top-color: #f59e0b; background-color: #fffbe6; }
    .ua-border { border-top-color: #8b5cf6; background-color: #f9f0ff; }
    .vanbree-border { border-top-color: #06b6d4; background-color: #e6fffb; }
    .total-border { border-top-color: #64748b; background-color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন (Streamlit Secrets) ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_all_data():
    client = get_gspread_client()
    
    # শিট আইডি সমূহ
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    # ডাটা পড়া (DATA এবং FINAL SUMMARY ট্যাব থেকে)
    df_m = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_y = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    # এরর ফিক্স: ডাটা টাইপ ক্লিন করা (Serialization error এড়াতে)
    for d in [df_m, df_y]:
        d.columns = [c.strip() for c in d.columns]
        # সব কলামকে প্রথমে স্ট্রিং করে তারপর সংখ্যায় রূপান্তর করা নিরাপদ
        for col in d.columns:
            if col in ['Time', 'SQM', 'Orders', 'Order', 'FLOOR PLAN', 'MEASUREMENT', 'WORKING DAY', 'AVG TIME']:
                d[col] = pd.to_numeric(d[col], errors='coerce').fillna(0)
            elif col in ['date', 'Date', 'Ticket ID', 'Floor']:
                d[col] = d[col].astype(str).replace('0', '')
    
    return df_m, df_y

try:
    df_master, df_yearly = load_all_data()

    # --- ৩. ন্যাভিগেশন ও ফিল্টার ---
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Dashboard View", ["Dashboard", "Yearly Artist Profile", "Tracking System"])
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("## 🔍 Global Filters")
    
    # মাস্টার ডাটার তারিখ ফিল্টার
    df_master['date_dt'] = pd.to_datetime(df_master['date'], errors='coerce')
    start_date = st.sidebar.date_input("Start Date", df_master['date_dt'].min().date())
    end_date = st.sidebar.date_input("End Date", df_master['date_dt'].max().date())
    
    mask = (df_master['date_dt'].dt.date >= start_date) & (df_master['date_dt'].dt.date <= end_date)
    df = df_master[mask].copy()

    # --- ৪. ম্যান-ডে ক্যালকুলেশন লজিক ---
    def get_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৫. মেইন ড্যাশবোর্ড ---
    if page == "Dashboard":
        st.markdown("<h2 style='text-align: center;'>Performance Analytics 2025</h2>", unsafe_allow_html=True)
        
        # ৭টি কার্ড মেট্রিক্স
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2>{get_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab_team, tab_artist = st.tabs(["👥 Team Summary", "🎨 Artist Summary Breakdown"])
        
        with tab_team:
            st.subheader("Team Wise Performance")
            team_sum = df.groupby(['Team', 'Shift']).agg(Artists=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Time=('Time', 'sum')).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)

        with tab_artist:
            st.subheader("Artist summary (Aggregated)")
            artist_sum = df.groupby(['Name', 'Team', 'Shift']).agg(Order=('Ticket ID', 'count'), Time=('Time', 'sum'), days=('date', 'nunique')).reset_index()
            artist_sum['Idle'] = (artist_sum['days'] * 400) - artist_sum['Time']
            artist_sum['Idle'] = artist_sum['Idle'].apply(lambda x: max(0, x))
            st.dataframe(artist_sum.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=600)

    # --- ৬. Yearly Profile ট্যাব ---
    elif page == "Yearly Artist Profile":
        st.title("👤 Artist Yearly Performance")
        
        all_artists = sorted(df_yearly['USER NAME ALL'].unique().tolist())
        artist_sel = st.selectbox("Search Artist Name", all_artists)
        y_data = df_yearly[df_yearly['USER NAME ALL'] == artist_sel]
        
        if not y_data.empty:
            d = y_data.iloc[0]
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Yearly FP Done", d['FLOOR PLAN'])
            c2.metric("Yearly MRP Done", d['MEASUREMENT'])
            c3.metric("Avg working time", f"{d['AVG TIME']}m")
            c4.metric("Days Worked", d['WORKING DAY'])
            
            st.markdown("---")
            # বার চার্ট (আপনার রিকোয়েস্ট অনুযায়ী)
            st.subheader("Annual Production Breakdown")
            chart_df = pd.DataFrame({
                'Spec': ['FP', 'MRP', 'CAD', 'UA', 'VanBree'],
                'Count': [d['FLOOR PLAN'], d['MEASUREMENT'], d['AUTO CAD'], d['URBAN ANGLES'], d['VanBree Media']]
            })
            st.plotly_chart(px.bar(chart_df, x='Spec', y='Count', color='Spec', text='Count'), use_container_width=True)
            st.write(f"Assigned Team: {d['Team']}")
        else:
            st.warning("No yearly summary data found for this artist.")

    # --- ৭. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("🎯 Performance Tracking")
        # Ticket ID এর পাশে লিঙ্ক তৈরি করে দেখানো
        tdf = df.copy()
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        st.dataframe(tdf, column_config={"RT Link": st.column_config.LinkColumn("Open Ticket")}, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
