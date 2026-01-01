import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটআপ ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

# CSS স্টাইল (কার্ড ডিজাইনের জন্য)
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

@st.cache_data(ttl=300) # ডাটা ৫ মিনিট পর পর রিফ্রেশ হবে
def get_data():
    client = get_gspread_client()
    sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    spreadsheet = client.open_by_key(sheet_id)
    df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
    
    # কলামের স্পেস ক্লিন করা
    df.columns = [c.strip() for c in df.columns]
    
    # ডাটা টাইপ কনভার্ট করা
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    
    if 'Floor' in df.columns: df['Floor'] = df['Floor'].astype(str)
    if 'Ticket ID' in df.columns: df['Ticket ID'] = df['Ticket ID'].astype(str)
        
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
    product_selected = st.sidebar.selectbox("Product Type Filter", ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"])

    # ডাটা ফিল্টারিং (Date, Team, Shift অনুযায়ী)
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_selected != "All": mask &= (df_raw['Product'] == product_selected)
    df = df_raw[mask].copy()

    # মেইন ক্যালকুলেশন ফাংশন
    def calculate_man_day_avg(target_df, product_name, job_type="Live Job"):
        subset = target_df[(target_df['Product'] == product_name) & (target_df['Job Type'] == job_type)]
        if subset.empty: return 0.0
        total_tasks = len(subset)
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৪. মেইন ড্যাশবোর্ড ---
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
        col_left, col_right = st.columns([1.8, 1])

        with col_left:
            st.subheader("Team Summary")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum())
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            
            st.subheader("Performance Breakdown (Artist Summary)")
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
            artist_breakdown['Idle'] = (artist_breakdown['worked_days'] * 400) - artist_breakdown['Time']
            artist_breakdown['Idle'] = artist_breakdown['Idle'].apply(lambda x: max(0, x))
            artist_breakdown = artist_breakdown.sort_values(by=['Order', 'Time'], ascending=False)
            
            cols_order = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'VanBree', 'SQM']
            st.dataframe(artist_breakdown[cols_order], use_container_width=True, hide_index=True)

        # --- ডানপাশের কলাম যেখানে আপনার কাঙ্ক্ষিত পরিবর্তন করা হয়েছে ---
        with col_right:
            unique_artist_list = sorted(df['Name'].unique().tolist())
            if not artist_breakdown.empty:
                top_performer_name = artist_breakdown.iloc[0]['Name']
                default_idx = unique_artist_list.index(top_performer_name) if top_performer_name in unique_artist_list else 0
            else: default_idx = 0

            artist_selected = st.selectbox("Select Artist for Stats", unique_artist_list, index=default_idx)
            
            # ডাটা ফিল্টার
            artist_df = df[df['Name'] == artist_selected]
            
            if not artist_df.empty:
                st.subheader(f"Total Projects Done: {artist_selected}")
                
                # ১. শুধুমাত্র প্রজেক্ট সংখ্যা বের করা (Count of Entries)
                # এখানে .size() ব্যবহার করায় এটি শুধু রো (Row) সংখ্যা গুনবে, 'Time' এর ভ্যালু নিবে না।
                project_distribution = artist_df.groupby('Product').size().reset_index(name='Total Projects')
                
                # ২. বার চার্ট তৈরি (Bar Chart)
                bar_fig = px.bar(
                    project_distribution, 
                    x='Product', 
                    y='Total Projects',
                    text='Total Projects', # বারের মাথায় সংখ্যা দেখাবে
                    color='Product',
                    height=400,
                    labels={'Total Projects': 'Number of Projects', 'Product': 'Category'}
                )
                
                bar_fig.update_traces(textposition='outside')
                bar_fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Number of Projects")
                
                # চার্ট ডিসপ্লে
                st.plotly_chart(bar_fig, use_container_width=True)
                
                # আর্টিস্টের কাজের ডিটেইলস টেবিল
                st.subheader("Artist Performance Detail")
                detail_cols = ['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']
                detail_t = artist_df[[c for c in detail_cols if c in artist_df.columns]].copy()
                detail_t['date'] = detail_t['date'].astype(str)
                st.dataframe(detail_t, use_container_width=True, hide_index=True)

    # --- ৫. পারফরম্যান্স ট্র্যাকিং পেজ ---
    elif page == "Performance Tracking":
        st.title("🎯 PERFORMANCE TRACKING")
        criteria = st.selectbox("Criteria Selection", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        
        tdf_calc = df.copy()
        short_ip_mask = (((tdf_calc['Employee Type'] == 'QC') & (tdf_calc['Time'] < 2)) | ((tdf_calc['Employee Type'] == 'Artist') & (((tdf_calc['Product'] == 'Floorplan Queue') & (tdf_calc['Time'] <= 15)) | ((tdf_calc['Product'] == 'Measurement Queue') & (tdf_calc['Time'] < 5)) | (~tdf_calc['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf_calc['Time'] <= 10)))))
        spending_more_mask = (((tdf_calc['Employee Type'] == 'QC') & (tdf_calc['Time'] > 20)) | ((tdf_calc['Employee Type'] == 'Artist') & ((tdf_calc['Time'] >= 150) | ((tdf_calc['Product'] == 'Measurement Queue') & (tdf_calc['Time'] > 40)))))
        high_time_sqm_mask = (tdf_calc['Time'] > (tdf_calc['SQM'] + 15)) & ~spending_more_mask

        final_mask = pd.Series([True] * len(tdf_calc))
        if criteria == "Short IP": final_mask = short_ip_mask
        elif criteria == "Spending More Time": final_mask = spending_more_mask
        elif criteria == "High Time vs SQM": final_mask = high_time_sqm_mask

        st.metric("Total Jobs Found", len(tdf_calc[final_mask]))
        track_df = tdf_calc[final_mask].copy()
        track_df['date'] = track_df['date'].astype(str)
        st.dataframe(track_df, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Something went wrong: {e}")
