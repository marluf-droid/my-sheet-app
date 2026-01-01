import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটআপ ও ডিজাইন ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

st.markdown("""
    <style>
    .metric-card { padding: 15px; border-radius: 8px; text-align: center; color: #333; font-weight: bold; margin-bottom: 10px; border-bottom: 4px solid #ddd; }
    .rework-card { background-color: #FFEBEE; border-color: #F44336; }
    .fp-card { background-color: #E3F2FD; border-color: #2196F3; }
    .mrp-card { background-color: #E8F5E9; border-color: #4CAF50; }
    .cad-card { background-color: #FFFDE7; border-color: #FBC02D; }
    .ua-card { background-color: #F3E5F5; border-color: #9C27B0; }
    .vanbree-card { background-color: #E0F2F1; border-color: #009688; }
    .total-card { background-color: #ECEFF1; border-color: #607D8B; }
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
def get_data():
    client = get_gspread_client()
    sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    spreadsheet = client.open_by_key(sheet_id)
    df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
    
    # কলামের নাম ক্লিন করা
    df.columns = [c.strip() for c in df.columns]
    
    # ডাটা টাইপ কনভার্ট করা
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    
    # টেক্সট ক্লিন করা (বাড়তি স্পেস রিমুভ)
    text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
            
    return df

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ন্যাভিগেশন ও গ্লোবাল ফিল্টার ---
    st.sidebar.markdown("# 🧭 Navigation")
    page = st.sidebar.radio("Select Dashboard", ["Main Dashboard", "Performance Tracking"])
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("# 🔍 Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_list = ["All"] + sorted(df_raw['Team'].unique().tolist())
    team_selected = st.sidebar.selectbox("Team Name", team_list)
    
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
    
    # Product Type Filter
    product_list = ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"]
    product_selected_global = st.sidebar.selectbox("Product Type Filter", product_list)

    # ডাটা ফিল্টারিং (Global Mask)
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_selected_global != "All": mask &= (df_raw['Product'] == product_selected_global)
    df = df_raw[mask].copy()

    # --- ৪. ম্যান-ডে এভারেজ ক্যালকুলেশন (গুগল শিট ফর্মুলা অনুযায়ী) ---
    def calculate_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        total_tasks = len(subset)
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৫. মেইন ড্যাশবোর্ড পেজ ---
    if page == "Main Dashboard":
        st.title("📊 PERFORMANCE ANALYTICS 2025")
        
        # কার্ড মেট্রিক্স
        avg_rework = calculate_man_day_avg(df, "Floorplan Queue", "Rework")
        avg_fp = calculate_man_day_avg(df, "Floorplan Queue", "Live Job")
        avg_mrp = calculate_man_day_avg(df, "Measurement Queue", "Live Job")
        avg_cad = calculate_man_day_avg(df, "Autocad Queue", "Live Job")
        avg_ua = calculate_man_day_avg(df, "Urban Angles", "Live Job")
        avg_vanbree = calculate_man_day_avg(df, "Van Bree Media", "Live Job")

        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.markdown(f'<div class="metric-card rework-card">Rework AVG<br><h2>{avg_rework}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{avg_fp}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{avg_mrp}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{avg_cad}</h2></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{avg_ua}</h2></div>', unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{avg_vanbree}</h2></div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([2, 1])

        with col_left:
            # --- ৫.১ TEAM SUMMARY (এখন সব কলাম থাকবে) ---
            st.subheader("Team Summary")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                SQM=('SQM', 'sum')
            ).reset_index()
            # কলামগুলো সুন্দর করে সাজিয়ে দেখানো
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            
            # --- ৫.২ PERFORMANCE BREAKDOWN (আর্টিস্ট সামারি + Idle Time) ---
            st.subheader("Performance Breakdown Section (Artist Summary)")
            artist_breakdown = df.groupby(['Name', 'Team', 'Shift']).agg(
                Order=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                SQM=('SQM', 'sum'),
                worked_days=('date', 'nunique')
            ).reset_index()

            # Idle টাইম লজিক: (কাজ করা দিন * ৪০০) - মোট কাজের সময়
            artist_breakdown['Idle'] = (artist_breakdown['worked_days'] * 400) - artist_breakdown['Time']
            artist_breakdown['Idle'] = artist_breakdown['Idle'].apply(lambda x: max(0, x))
            
            # স্কোরিং লজিক অনুযায়ী সর্টিং
            artist_breakdown['Score'] = artist_breakdown['Order'] + (artist_breakdown['Time'] / 1000000)
            artist_breakdown = artist_breakdown.sort_values(by='Score', ascending=False)
            
            final_breakdown_cols = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'VanBree', 'SQM']
            st.dataframe(artist_breakdown[final_breakdown_cols], use_container_width=True, hide_index=True)

        with col_right:
            # --- ৫.৩ আর্টিস্ট স্ট্যাটাস ও পাই চার্ট ---
            unique_names = sorted(df['Name'].unique().tolist())
            top_name = artist_breakdown.iloc[0]['Name'] if not artist_breakdown.empty else ""
            artist_selected = st.selectbox("Select Artist for Stats", unique_names, index=unique_names.index(top_name) if top_name in unique_names else 0)
            
            artist_df = df[df['Name'] == artist_selected]
            if not artist_df.empty:
                st.subheader(f"Stats: {artist_selected}")
                pie_data = artist_df['Product'].value_counts().reset_index()
                pie_data.columns = ['Product', 'Unique Orders']
                fig = px.pie(pie_data, values='Unique Orders', names='Product', hole=0.5, height=350)
                fig.update_traces(textinfo='value+label')
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Artist Performance Detail")
                detail_df = artist_df.copy()
                detail_df['date'] = detail_df['date'].apply(lambda x: x.strftime('%m/%d/%Y'))
                # সব কলাম সাজানো (Floor, Labels সহ)
                detail_cols = ['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']
                st.dataframe(detail_df[detail_cols].rename(columns={'date':'Date', 'Ticket ID':'Order ID'}), use_container_width=True, hide_index=True)

    # --- ৬. পারফরম্যান্স ট্র্যাকিং পেজ ---
    elif page == "Performance Tracking":
        st.title("🎯 PERFORMANCE TRACKING")
        criteria = st.selectbox("Criteria Selection", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        
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
