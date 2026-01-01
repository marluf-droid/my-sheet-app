import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ও স্মার্ট ডিজাইন ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

# আধুনিক CSS (Sleek UI)
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    .metric-card { 
        padding: 20px; border-radius: 15px; text-align: center; color: #1e293b; 
        background: #ffffff; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
    }
    .rework-card { border-top: 6px solid #ef4444; }
    .fp-card { border-top: 6px solid #3b82f6; }
    .mrp-card { border-top: 6px solid #10b981; }
    .cad-card { border-top: 6px solid #f59e0b; }
    .ua-card { border-top: 6px solid #8b5cf6; }
    .vanbree-card { border-top: 6px solid #06b6d4; }
    .total-card { border-top: 6px solid #64748b; }
    
    h3 { color: #0f172a; font-size: 1.2rem; font-weight: 700; margin-bottom: 15px; }
    .stTabs [data-baseweb="tab"] { font-weight: 600; font-size: 16px; color: #64748b; }
    .stTabs [aria-selected="true"] { color: #3b82f6 !important; border-bottom-color: #3b82f6 !important; }
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
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
    for col in text_cols:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()
    return df

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ন্যাভিগেশন ও গ্লোবাল ফিল্টারস ---
    st.sidebar.markdown("### 🧭 Navigation")
    page = st.sidebar.radio("Select Dashboard", ["Main Dashboard", "Performance Tracking"])
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("### 🔍 Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_selected = st.sidebar.selectbox("Team Name", ["All"] + sorted(df_raw['Team'].unique().tolist()))
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
    product_selected_global = st.sidebar.selectbox("Product Type Filter", ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"])

    # ডাটা ফিল্টারিং
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_selected_global != "All": mask &= (df_raw['Product'] == product_selected_global)
    df = df_raw[mask].copy()

    # --- ৪. স্পেশাল এভারেজ ফাংশন (Man-Day Average) ---
    def get_avg(p_name, j_type="Live Job"):
        subset = df[(df['Product'] == p_name) & (df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        total_tasks = len(subset)
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৫. মেইন ড্যাশবোর্ড পেজ ---
    if page == "Main Dashboard":
        st.markdown("<h1 style='text-align: center; color: #0f172a;'>📊 Performance Analytics 2025</h1>", unsafe_allow_html=True)
        
        # স্মার্ট মেট্রিিক্স কার্ডস
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-card">Rework AVG<br><h2>{get_avg("Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{get_avg("Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{get_avg("Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{get_avg("Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{get_avg("Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{get_avg("Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📈 Overview & Trends", "👥 Detailed Team Summary", "🎨 Artist Insights"])

        with tab1:
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                st.subheader("Daily Productivity Chart")
                trend_df = df.groupby('date').size().reset_index(name='Orders')
                fig_trend = px.line(trend_df, x='date', y='Orders', markers=True, color_discrete_sequence=['#3b82f6'])
                st.plotly_chart(fig_trend, use_container_width=True)
            with col_t2:
                st.subheader("🏆 Leaderboard (Top 5)")
                lb = df.groupby('Name').size().sort_values(ascending=False).head(5)
                for i, (name, count) in enumerate(lb.items()):
                    st.info(f"{i+1}. **{name}** - {count} Orders")

        with tab2:
            # --- টিম সামারি (সব কলাম সহ) ---
            st.subheader("Team Wise Performance Detail")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                SQM=('SQM', 'sum')
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)

        with tab3:
            # --- পারফরম্যান্স ব্রেকডাউন (UNIQUE ARTIST SUMMARY) ---
            st.subheader("Artist Performance Summary (Collapsed)")
            artist_summary = df.groupby(['Name', 'Team', 'Shift']).agg(
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

            # Idle Time Logic: (Worked Days * 400) - Total Time
            artist_summary['Idle'] = (artist_summary['worked_days'] * 400) - artist_summary['Time']
            artist_summary['Idle'] = artist_summary['Idle'].apply(lambda x: max(0, x))
            
            # আপনার শিট স্কোরিং লজিক দিয়ে সর্টিং
            artist_summary['Score'] = artist_summary['Order'] + (artist_summary['Time'] / 1000000)
            artist_summary = artist_summary.sort_values(by='Score', ascending=False)
            
            final_cols = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'VanBree', 'SQM']
            st.dataframe(artist_summary[final_cols], use_container_width=True, hide_index=True)

            st.markdown("---")
            # ইন্ডিভিজুয়াল সিলেকশন
            u_names = sorted(df['Name'].unique().tolist())
            top_name = artist_summary['Name'].iloc[0] if not artist_summary.empty else ""
            a_sel = st.selectbox("Deep-Dive into Artist Stats", u_names, index=u_names.index(top_name) if top_name in u_names else 0)
            a_df = df[df['Name'] == a_sel]

            c_a1, c_a2 = st.columns([1, 1.5])
            with c_a1:
                p_data = a_df['Product'].value_counts().reset_index()
                p_data.columns = ['Product', 'Unique Orders']
                fig_pie = px.pie(p_data, values='Unique Orders', names='Product', hole=0.5, title=f"Stats: {a_sel}")
                fig_pie.update_traces(textinfo='value+label')
                st.plotly_chart(fig_pie, use_container_width=True)
            with c_a2:
                st.write("Performance Log (All Columns)")
                log_df = a_df.copy()
                log_df['date'] = log_df['date'].apply(lambda x: x.strftime('%m/%d/%Y'))
                st.dataframe(log_df[['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time']], use_container_width=True, hide_index=True)

    # --- ৬. ট্র্যাকিং পেজ ---
    elif "Tracking" in page:
        st.title("🎯 Performance Tracking")
        criteria = st.selectbox("Filter by Criteria", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        
        s_ip = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | ((tdf['Employee Type'] == 'Artist') & (((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) | (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10)))))
        s_mt = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | ((tdf['Employee Type'] == 'Artist') & ((tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40)))))
        h_ts = (tdf['Time'] > (tdf['SQM'] + 15)) & ~s_mt

        if criteria == "Short IP": tdf = tdf[s_ip]
        elif criteria == "Spending More Time": tdf = tdf[s_mt]
        elif criteria == "High Time vs SQM": tdf = tdf[h_ts]

        st.metric("Jobs Found", len(tdf))
        st.dataframe(tdf, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Something went wrong: {e}")
