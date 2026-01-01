import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটআপ ও ডিজাইন ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

# কালারফুল কার্ডের জন্য CSS
st.markdown("""
    <style>
    .metric-card { padding: 15px; border-radius: 8px; text-align: center; color: #333; font-weight: bold; margin-bottom: 10px; }
    .fp-card { background-color: #E3F2FD; border-top: 5px solid #2196F3; }
    .mrp-card { background-color: #E8F5E9; border-top: 5px solid #4CAF50; }
    .cad-card { background-color: #FFFDE7; border-top: 5px solid #FBC02D; }
    .rework-card { background-color: #FFEBEE; border-top: 5px solid #F44336; }
    .ua-card { background-color: #F3E5F5; border-top: 5px solid #9C27B0; }
    .vanbree-card { background-color: #E0F2F1; border-top: 5px solid #009688; }
    .total-card { background-color: #ECEFF1; border-top: 5px solid #607D8B; }
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
    df.columns = [c.strip() for c in df.columns] # কলামের নাম ক্লিন করা
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    return df

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ন্যাভিগেশন ও ফিল্টার ---
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
    
    product_list = ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"]
    product_selected = st.sidebar.selectbox("Product Type Filter", product_list)

    # --- ৪. ডাটা ফিল্টারিং ---
    mask = (df_raw['date'].dt.date >= start_date) & (df_raw['date'].dt.date <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_selected != "All": mask &= (df_raw['Product'] == product_selected)
    df = df_raw[mask]

    # --- ৫. Select Log Name (Artist/QC) ফিল্টার পুনরায় যোগ করা হয়েছে ---
    artist_names = sorted(df['Name'].unique().tolist())
    artist_selected = st.sidebar.selectbox("Select Log Name (Artist/QC)", ["Default (Top)"] + artist_names)

    # --- ৬. মেইন ড্যাশবোর্ড পেজ ---
    if page == "Main Dashboard":
        st.title("📊 PERFORMANCE ANALYTICS 2025")
        
        def get_avg(p_name):
            subset = df[df['Product'] == p_name]
            return round(subset['Time'].mean(), 2) if not subset.empty else 0.0

        # কালারফুল কার্ড
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{get_avg("Floorplan Queue")}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{get_avg("Measurement Queue")}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{get_avg("Autocad Queue")}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card rework-card">Rework<br><h2>{get_avg("Rework")}</h2></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{get_avg("Urban Angles")}</h2></div>', unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{get_avg("Van Bree Media")}</h2></div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        col_left, col_right = st.columns([1.6, 1])

        with col_left:
            # Team Summary (CAD এবং UA সহ)
            st.subheader("Team Summary")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum())
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            
            st.subheader("Performance Breakdown Section")
            st.dataframe(df.head(200), use_container_width=True, hide_index=True)

        with col_right:
            # ইন্ডিভিজুয়াল আর্টিস্ট ক্যালকুলেশন
            if artist_selected == "Default (Top)" and not df.empty:
                final_artist = df.groupby('Name')['Ticket ID'].count().sort_values(ascending=False).index[0]
            else:
                final_artist = artist_selected

            st.subheader(f"Stats: {final_artist}")
            artist_df = df[df['Name'] == final_artist]
            
            if not artist_df.empty:
                fig = px.pie(artist_df, values='Ticket ID', names='Product', hole=0.5, height=350)
                fig.update_traces(textinfo='value+label')
                st.plotly_chart(fig, use_container_width=True)
                
                st.subheader("Individual Performance Detail")
                detail_t = artist_df[['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']].copy()
                if 'date' in detail_t.columns: detail_t['date'] = detail_t['date'].dt.strftime('%m/%d/%Y')
                detail_t.columns = ['Date', 'Order ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']
                st.dataframe(detail_t, use_container_width=True, hide_index=True)
            else:
                st.info("No data found for this selection.")

    # --- ৭. পারফরম্যান্স ট্র্যাকিং পেজ (QUERY লজিক) ---
    elif page == "Performance Tracking":
        st.title("🎯 PERFORMANCE TRACKING")
        criteria = st.selectbox("Criteria Selection", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        
        tdf = df.copy()
        
        # জটিল কন্ডিশন মাস্কিং
        short_ip_mask = (
            ((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) |
            ((tdf['Employee Type'] == 'Artist') & (
                ((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) |
                ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) |
                (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10))
            ))
        )
        spending_more_mask = (
            ((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) |
            ((tdf['Employee Type'] == 'Artist') & (
                (tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40))
            ))
        )
        high_time_sqm_mask = (tdf['Time'] > (tdf['SQM'] + 15)) & ~spending_more_mask

        if criteria == "Short IP": tdf = tdf[short_ip_mask]
        elif criteria == "Spending More Time": tdf = tdf[spending_more_mask]
        elif criteria == "High Time vs SQM": tdf = tdf[high_time_sqm_mask]

        tk1, tk2, tk3, tk4 = st.columns(4)
        tk1.metric("Total Order", len(tdf))
        tk2.metric("Avg. Time FP", round(tdf[tdf['Product']=='Floorplan Queue']['Time'].mean(), 1) if not tdf[tdf['Product']=='Floorplan Queue'].empty else 0)
        tk3.metric("Avg. Time MRP", round(tdf[tdf['Product']=='Measurement Queue']['Time'].mean(), 1) if not tdf[tdf['Product']=='Measurement Queue'].empty else 0)
        tk4.metric("Unique Artists", tdf['Name'].nunique())

        st.markdown("---")
        st.write(f"Results for **{criteria}**: {len(tdf)} items found.")
        st.dataframe(tdf, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error loading dashboard: {e}")
