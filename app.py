import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# ১. পেজ সেটআপ
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

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

# ২. ডাটা কানেকশন (Streamlit Secrets থেকে ডাটা নেওয়া)
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    # Secrets থেকে JSON_KEY পড়ে JSON-এ রূপান্তর করা হচ্ছে
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)
    creds_dict = dict(st.secrets["gcp_service_account"])
    # private_key এর ভেতরের \n ঠিক করা
    creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def get_data():
    client = get_gspread_client()
    sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    spreadsheet = client.open_by_key(sheet_id)
    df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
    
    # ডাটা ক্লিনিং
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    df.columns = [c.strip() for c in df.columns]
    return df

try:
    df_raw = get_data()

    # --- সাইডবার ফিল্টারস ---
    st.sidebar.title("Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_selected = st.sidebar.selectbox("Team Name", ["All"] + sorted(df_raw['Team'].unique().tolist()))
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All"] + sorted(df_raw['Employee Type'].unique().tolist()))
    product_selected = st.sidebar.selectbox("Product Type Filter", ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"])

    # ফিল্টারিং লজিক
    mask = (df_raw['date'].dt.date >= start_date) & (df_raw['date'].dt.date <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_selected != "All": mask &= (df_raw['Product'] == product_selected)
    df = df_raw[mask]

    # টপ আর্টিস্ট লজিক
    if not df.empty:
        top_perf = df.groupby('Name').agg({'Ticket ID':'count', 'Time':'sum'}).sort_values(by=['Ticket ID', 'Time'], ascending=False)
        default_artist = top_perf.index[0]
    else: default_artist = "None"

    artist_selected = st.sidebar.selectbox("Select Log Name (Artist/QC)", ["Default (Top)"] + sorted(df['Name'].unique().tolist()))
    final_artist = default_artist if artist_selected == "Default (Top)" else artist_selected

    # --- মেইন ড্যাশবোর্ড ---
    st.title("📊 PERFORMANCE ANALYTICS 2025")
    
    def get_avg(p_name):
        subset = df[df['Product'] == p_name]
        return round(subset['Time'].mean(), 2) if not subset.empty else 0.0

    # কার্ড লেআউট
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{get_avg("Floorplan Queue")}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{get_avg("Measurement Queue")}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{get_avg("Autocad Queue")}</h2></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card rework-card">Rework<br><h2>{get_avg("Rework")}</h2></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{get_avg("Urban Angles")}</h2></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{get_avg("Van Bree Media")}</h2></div>', unsafe_allow_html=True)
    with c7: st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    col_left, col_right = st.columns([1.5, 1])

    with col_left:
        st.subheader("Team Summary")
        team_sum = df.groupby(['Team', 'Shift']).agg(
            Present=('Name', 'nunique'),
            Total_Orders=('Ticket ID', 'count'),
            Total_Time=('Time', 'sum'),
            CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
            UA=('Product', lambda x: (x == 'Urban Angles').sum())
        ).reset_index()
        st.dataframe(team_sum, use_container_width=True, hide_index=True)
        
        st.subheader("Performance Breakdown Section")
        st.dataframe(df.head(200), use_container_width=True, hide_index=True)

    with col_right:
        st.subheader(f"Stats: {final_artist}")
        artist_df = df[df['Name'] == final_artist]
        if not artist_df.empty:
            pie_data = artist_df['Product'].value_counts().reset_index()
            pie_data.columns = ['Product', 'Count']
            fig = px.pie(pie_data, values='Count', names='Product', hole=0.5, height=350)
            fig.update_traces(textinfo='value+label')
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Individual Performance Detail")
            cols_to_show = ['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']
            existing_cols = [c for c in cols_to_show if c in artist_df.columns]
            detail_t = artist_df[existing_cols].copy()
            if 'date' in detail_t.columns: detail_t['date'] = detail_t['date'].dt.strftime('%m/%d/%Y')
            detail_t.columns = ['Date', 'Order ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']
            st.dataframe(detail_t, use_container_width=True, hide_index=True)
        else: st.info("No data found.")

except Exception as e:
    st.error(f"Error loading dashboard: {e}")






