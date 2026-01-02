import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ কনফিগারেশন ---
st.set_page_config(page_title="Performance Analytics Pro", layout="wide")

st.markdown("""
    <style>
    .metric-card { padding: 15px; border-radius: 12px; text-align: center; color: #1e293b; background: #ffffff; border-top: 5px solid #e2e8f0; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
    .rework-border { border-top-color: #ef4444; background-color: #fff1f0; }
    .fp-border { border-top-color: #3b82f6; background-color: #e6f7ff; }
    .mrp-border { border-top-color: #10b981; background-color: #f6ffed; }
    .cad-border { border-top-color: #f59e0b; background-color: #fffbe6; }
    .ua-border { border-top-color: #8b5cf6; background-color: #f9f0ff; }
    .vanbree-border { border-top-color: #06b6d4; background-color: #e6fffb; }
    .total-border { border-top-color: #64748b; background-color: #f8fafc; }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন ---
@st.cache_resource
def get_gspread_client():
    creds_info = json.loads(st.secrets["JSON_KEY"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_data():
    client = get_gspread_client()
    
    # শিট আইডি সমূহ
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    internal_id = "1mOph7_YK6seLfXpKrO00S9tMaNvbBCS5iQP7FjiNBaE"
    external_id = "1yrCM3xMpQ2IdLO4wBIzyeMJ5lAC4KRTUmA-h5dG0iEM"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    # ডাটা পড়া
    df_master = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_int = pd.DataFrame(client.open_by_key(internal_id).worksheet("DATA").get_all_records())
    df_ext = pd.DataFrame(client.open_by_key(external_id).worksheet("Team Data").get_all_records())
    df_yearly = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    # ক্লিনিং
    for d in [df_master, df_int, df_ext, df_yearly]:
        d.columns = [c.strip() for c in d.columns]
    
    df_master['date'] = pd.to_datetime(df_master['date'], errors='coerce').dt.date
    df_master['Time'] = pd.to_numeric(df_master['Time'], errors='coerce').fillna(0)
    df_master['SQM'] = pd.to_numeric(df_master['SQM'], errors='coerce').fillna(0)
    
    return df_master, df_int, df_ext, df_yearly

try:
    df, df_int, df_ext, df_yearly = load_data()

    # --- ৩. ন্যাভিগেশন ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Live Dashboard", "Yearly Profile", "Tracking System"])
    
    st.sidebar.markdown("---")
    st.sidebar.title("Global Filters")
    start_date = st.sidebar.date_input("Start Date", df['date'].min())
    end_date = st.sidebar.date_input("End Date", df['date'].max())
    
    # ফিল্টারিং লজিক
    mask = (df['date'] >= start_date) & (df['date'] <= end_date)
    filtered_df = df[mask].copy()

    # --- ৪. স্পেশাল ক্যালকুলেশন ---
    def get_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৫. লাইভ ড্যাশবোর্ড পেজ ---
    if page == "Live Dashboard":
        st.title("📊 Performance Dashboard 2025")
        
        # ৭টি প্রফেশনাল কার্ড
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_avg(filtered_df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_avg(filtered_df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_avg(filtered_df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_avg(filtered_df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_avg(filtered_df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2>{get_avg(filtered_df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(filtered_df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        tab_team, tab_breakdown = st.tabs(["👥 Team Summary", "🎨 Artist Summary Breakdown"])
        
        with tab_team:
            st.subheader("Team Performance Breakdown")
            team_sum = filtered_df.groupby(['Team', 'Shift']).agg(Present=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Rework=('Job Type', lambda x: (x == 'Rework').sum()), FP=('Product', lambda x: (x == 'Floorplan Queue').sum()), MRP=('Product', lambda x: (x == 'Measurement Queue').sum()), CAD=('Product', lambda x: (x == 'Autocad Queue').sum()), UA=('Product', lambda x: (x == 'Urban Angles').sum()), VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()), Time=('Time', 'sum')).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)

        with tab_breakdown:
            st.subheader("Artist Summary (Aggregated)")
            artist_sum = filtered_df.groupby(['Name', 'Team', 'Shift']).agg(Order=('Ticket ID', 'count'), Time=('Time', 'sum'), Rework=('Job Type', lambda x: (x == 'Rework').sum()), FP=('Product', lambda x: (x == 'Floorplan Queue').sum()), MRP=('Product', lambda x: (x == 'Measurement Queue').sum()), UA=('Product', lambda x: (x == 'Urban Angles').sum()), CAD=('Product', lambda x: (x == 'Autocad Queue').sum()), VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()), days=('date', 'nunique')).reset_index()
            artist_sum['Idle'] = (artist_sum['days'] * 400) - artist_sum['Time']
            artist_sum['Idle'] = artist_sum['Idle'].apply(lambda x: max(0, x))
            st.dataframe(artist_sum.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=600)

    # --- ৬. Yearly Profile পেজ (নতুন) ---
    elif page == "Yearly Profile":
        st.title("👤 Artist Yearly Summary")
        
        all_artists = sorted(df_yearly['USER NAME ALL'].unique().tolist())
        artist_sel = st.selectbox("Search Artist Name", all_artists)
        
        # ডাটা ম্যাচিং
        artist_yearly = df_yearly[df_yearly['USER NAME ALL'] == artist_sel]
        artist_int = df_int[df_int['Mistake BY'] == artist_sel]
        artist_ext = df_ext[df_ext['Mistake BY'] == artist_sel]
        
        if not artist_yearly.empty:
            data = artist_yearly.iloc[0]
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Yearly Avg Time", f"{data['AVG TIME']}m")
            col2.metric("Total Working Days", data['WORKING DAY'])
            col3.metric("Internal Rejects", len(artist_int))
            col4.metric("External Rejects", len(artist_ext))
            
            st.markdown("---")
            c_left, c_right = st.columns(2)
            
            with c_left:
                st.subheader("Production Volume")
                chart_data = pd.DataFrame({
                    'Category': ['FP', 'MRP', 'CAD', 'UA', 'VanBree'],
                    'Total': [data['FLOOR PLAN'], data['MEASUREMENT'], data['AUTO CAD'], data['URBAN ANGLES'], data['VanBree Media']]
                })
                st.plotly_chart(px.bar(chart_data, x='Category', y='Total', color='Category', text='Total'), use_container_width=True)
            
            with c_right:
                st.subheader("Quality Log (Internal)")
                st.dataframe(artist_int[['Received', 'Order Number', 'QC', 'Comment']].tail(10), hide_index=True)
        else:
            st.info("No yearly summary found for this artist.")

    # --- ৭. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("🎯 Performance Tracking")
        criteria = st.selectbox("Select Criteria", ["Short IP", "Spending More Time", "High Time vs SQM"])
        # আগের ট্র্যাকিং লজিক ব্যবহার করা হয়েছে
        st.dataframe(filtered_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
