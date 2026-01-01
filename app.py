import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ---
st.set_page_config(page_title="Analytics 2025", layout="wide")

# প্রফেশনাল ডিজাইন স্টাইল
st.markdown("""
    <style>
    .main { background-color: #f5f7f9; }
    .metric-card { padding: 15px; border-radius: 10px; text-align: center; color: #333; font-weight: bold; box-shadow: 2px 2px 5px rgba(0,0,0,0.05); }
    .rework-card { background-color: #fff1f0; border-left: 5px solid #ff4d4f; }
    .fp-card { background-color: #e6f7ff; border-left: 5px solid #1890ff; }
    .mrp-card { background-color: #f6ffed; border-left: 5px solid #52c41a; }
    .cad-card { background-color: #fffbe6; border-left: 5px solid #faad14; }
    .ua-card { background-color: #f9f0ff; border-left: 5px solid #722ed1; }
    .vanbree-card { background-color: #e6fffb; border-left: 5px solid #13c2c2; }
    .total-card { background-color: #f5f5f5; border-left: 5px solid #595959; }
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
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
    for col in text_cols:
        if col in df.columns: df[col] = df[col].astype(str).str.strip()
    return df

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ফিল্টারস ---
    st.sidebar.title("🧭 Navigation")
    page = st.sidebar.radio("Dashboard Mode", ["Live Dashboard", "Performance Tracking"])
    
    st.sidebar.markdown("---")
    st.sidebar.title("🔍 Filters")
    start_date = st.sidebar.date_input("From", df_raw['date'].min())
    end_date = st.sidebar.date_input("To", df_raw['date'].max())
    
    team_selected = st.sidebar.selectbox("Team Name", ["All"] + sorted(df_raw['Team'].unique().tolist()))
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
    product_selected_global = st.sidebar.selectbox("Product Filter", ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"])

    # ডাটা ফিল্টারিং
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_selected_global != "All": mask &= (df_raw['Product'] == product_selected_global)
    df = df_raw[mask].copy()

    # --- ৪. স্পেশাল ক্যালকুলেশন ফাংশন ---
    def calculate_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        total_tasks = len(subset)
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৫. মেইন ড্যাশবোর্ড পেইজ ---
    if page == Live Dashboard":
        st.title("📊 PERFORMANCE ANALYTICS 2025")

        # কালারফুল কার্ড সেকশন
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.markdown(f'<div class="metric-card rework-card">Rework AVG<br><h2>{calculate_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card fp-card">FP AVG<br><h2>{calculate_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card mrp-card">MRP AVG<br><h2>{calculate_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card cad-card">CAD AVG<br><h2>{calculate_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="metric-card ua-card">UA AVG<br><h2>{calculate_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="metric-card vanbree-card">Van Bree<br><h2>{calculate_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="metric-card total-card">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # ট্যাব সিস্টেম যোগ করা হয়েছে (গোছানোর জন্য)
        tab1, tab2, tab3 = st.tabs(["📈 General Overview", "👥 Team Analysis", "🎨 Artist Deep-Dive"])

        with tab1:
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                st.subheader("Performance Trend (Daily Orders)")
                trend_df = df.groupby('date').size().reset_index(name='Daily Orders')
                fig_trend = px.line(trend_df, x='date', y='Daily Orders', markers=True, template="plotly_white")
                st.plotly_chart(fig_trend, use_container_width=True)
            with col_t2:
                st.subheader("🏆 Top 3 Performer")
                top_3 = df.groupby('Name').size().sort_values(ascending=False).head(3)
                for i, (name, count) in enumerate(top_3.items()):
                    st.success(f"{i+1}. **{name}** - {count} Orders")

        with tab2:
            st.subheader("Team Performance Summary")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Artists=('Name', 'nunique'), Orders=('Ticket ID', 'count'), 
                Time=('Time', 'sum'), Rework=('Job Type', lambda x: (x == 'Rework').sum())
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            # ডাউনলোড বাটন
            csv = team_sum.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Team Data", data=csv, file_name="team_summary.csv", mime="text/csv")

        with tab3:
            # আর্টিস্ট সামারি টেবিল
            st.subheader("Performance Breakdown Section")
            artist_breakdown = df.groupby(['Name', 'Team', 'Shift']).agg(
                Order=('Ticket ID', 'count'), Time=('Time', 'sum'),
                SQM=('SQM', 'sum'), worked_days=('date', 'nunique')
            ).reset_index()
            artist_breakdown['Idle'] = (artist_breakdown['worked_days'] * 400) - artist_breakdown['Time']
            artist_breakdown['Idle'] = artist_breakdown['Idle'].apply(lambda x: max(0, x))
            
            st.dataframe(artist_breakdown.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True)

            st.markdown("---")
            # ইন্ডিভিজুয়াল আর্টিস্ট ডিটেইলস
            st.subheader("Individual Artist Deep-Dive")
            u_names = sorted(df['Name'].unique().tolist())
            a_sel = st.selectbox("Select Artist", u_names)
            a_df = df[df['Name'] == a_sel]
            
            c_a1, c_a2 = st.columns([1, 1.5])
            with c_a1:
                pie_fig = px.pie(a_df, values='Time', names='Product', hole=0.5, title=f"Time Spent: {a_sel}")
                st.plotly_chart(pie_fig, use_container_width=True)
            with c_a2:
                st.write("Recent Tasks")
                st.dataframe(a_df[['date', 'Ticket ID', 'Product', 'SQM', 'Time']].tail(10), hide_index=True)

    # --- ৬. পারফরম্যান্স ট্র্যাকিং পেজ ---
    elif page == "Performance Tracking":
        st.title("🎯 PERFORMANCE TRACKING")
        criteria = st.selectbox("Criteria Selection", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        
        # আপনার QUERY ফর্মুলা মাস্কিং
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
