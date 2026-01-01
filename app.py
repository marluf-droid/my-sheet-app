import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটআপ ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

st.markdown("""
    <style>
    .metric-card { padding: 15px; border-radius: 8px; text-align: center; color: #333; font-weight: bold; margin-bottom: 10px; border-bottom: 4px solid #ddd; }
    .fp-card { background-color: #E3F2FD; border-color: #2196F3; }
    .mrp-card { background-color: #E8F5E9; border-color: #4CAF50; }
    .cad-card { background-color: #FFFDE7; border-color: #FBC02D; }
    .rework-card { background-color: #FFEBEE; border-color: #F44336; }
    .ua-card { background-color: #F3E5F5; border-color: #9C27B0; }
    .vanbree-card { background-color: #E0F2F1; border-color: #009688; }
    .total-card { background-color: #ECEFF1; border-color: #607D8B; }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def get_data():
    client = get_gspread_client()
    sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    spreadsheet = client.open_by_key(sheet_id)
    df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
    df.columns = [c.strip() for c in df.columns]
    # সময় ছাড়া শুধু তারিখ রাখার জন্য
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    return df

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ফিল্টার ---
    st.sidebar.markdown("# 🧭 Navigation")
    page = st.sidebar.radio("Select Dashboard", ["Main Dashboard", "Performance Tracking"])
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("# 🔍 Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_selected = st.sidebar.selectbox("Team Name", ["All"] + sorted(df_raw['Team'].unique().tolist()))
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
    product_filter = st.sidebar.selectbox("Product Filter (Cards Only)", ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Urban Angles", "Van Bree Media"])

    # ডাটা ফিল্টারিং (Global)
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    df = df_raw[mask]

    # --- ৪. স্পেশাল ক্যালকুলেশন ফাংশন (গুগল শিট ফর্মুলা অনুযায়ী) ---
    def calculate_man_day_avg(target_df, product_name, job_type="Live Job"):
        # ফিল্টার: নির্দিষ্ট প্রোডাক্ট এবং জব টাইপ (Live Job/Rework)
        subset = target_df[(target_df['Product'] == product_name) & (target_df['Job Type'] == job_type)]
        
        if subset.empty:
            return 0.0
        
        total_tasks = len(subset)
        # Man Days = ইউনিক (Name + Date) এর সংখ্যা
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৫. মেইন ড্যাশবোর্ড ---
    if page == "Main Dashboard":
        st.title("📊 PERFORMANCE ANALYTICS 2025")
        
        # কার্ড মেট্রিক্স ক্যালকুলেশন
        avg_fp = calculate_man_day_avg(df, "Floorplan Queue", "Live Job")
        avg_mrp = calculate_man_day_avg(df, "Measurement Queue", "Live Job")
        avg_cad = calculate_man_day_avg(df, "Autocad Queue", "Live Job")
        avg_rework = calculate_man_day_avg(df, "Floorplan Queue", "Rework") # আপনার ফর্মুলা অনুযায়ী
        avg_ua = calculate_man_day_avg(df, "Urban Angles", "Live Job")
        avg_vanbree = calculate_man_day_avg(df, "Van Bree Media", "Live Job")

        # কালারফুল কার্ড রেন্ডারিং
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{avg_fp}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{avg_mrp}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{avg_cad}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card rework-card">Rework AVG<br><h2>{avg_rework}</h2></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{avg_ua}</h2></div>', unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{avg_vanbree}</h2></div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            st.subheader("Team Summary")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum())
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            st.subheader("Performance Breakdown Section")
            st.dataframe(df.head(200), use_container_width=True, hide_index=True)

        with col_right:
            top_artist = df.groupby('Name')['Ticket ID'].count().sort_values(ascending=False).index[0] if not df.empty else "None"
            artist_selected = st.sidebar.selectbox("Artist Detail Selection", sorted(df['Name'].unique().tolist()), index=0)
            artist_df = df[df['Name'] == artist_selected]
            
            if not artist_df.empty:
                st.subheader(f"Stats: {artist_selected}")
                fig = px.pie(artist_df, values='Ticket ID', names='Product', hole=0.5, height=350)
                fig.update_traces(textinfo='value+label')
                st.plotly_chart(fig, use_container_width=True)
                st.subheader("Individual Performance Detail")
                detail_t = artist_df[['date', 'Ticket ID', 'Product', 'SQM', 'Time']].copy()
                detail_t.columns = ['Date', 'ID', 'Product', 'SQM', 'Time']
                st.dataframe(detail_t, use_container_width=True, hide_index=True)

    # --- ৬. পারফরম্যান্স ট্র্যাকিং পেজ ---
    elif page == "Performance Tracking":
        st.title("🎯 PERFORMANCE TRACKING")
        criteria = st.selectbox("Criteria Selection", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        
        # আপনার QUERY ফর্মুলা অনুযায়ী কন্ডিশন
        short_ip_mask = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | ((tdf['Employee Type'] == 'Artist') & (((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) | (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10)))))
        spending_more_mask = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | ((tdf['Employee Type'] == 'Artist') & ((tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40)))))
        high_time_sqm_mask = (tdf['Time'] > (tdf['SQM'] + 15)) & ~spending_more_mask

        if criteria == "Short IP": tdf = tdf[short_ip_mask]
        elif criteria == "Spending More Time": tdf = tdf[spending_more_mask]
        elif criteria == "High Time vs SQM": tdf = tdf[high_time_sqm_mask]

        st.metric("Total Jobs Found", len(tdf))
        st.dataframe(tdf, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
