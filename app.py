import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ও স্মার্ট ডিজাইন ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

# এটি আপনার ড্যাশবোর্ডকে পুরোপুরি ক্লিন করবে (আইকন ও মেনু হাইড করার সবচেয়ে শক্তিশালী কোড)
st.markdown("""
    <style>
    /* ১. মেনু এবং হেডার পুরোপুরি হাইড করা */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* ২. স্ট্রীমলিট টুলবার (GitHub/Fork/Deploy বাটন) হাইড করা */
    div[data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    .stDeployButton {display:none !important;}
    
    /* ৩. আধুনিক ফন্ট এবং মেট্রিক কার্ড ডিজাইন */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .metric-card {
        padding: 20px; border-radius: 12px; text-align: center; color: #1e293b;
        background: #ffffff; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
    }
    .rework-border { border-top: 5px solid #ef4444; background-color: #fff1f0; }
    .fp-border { border-top: 5px solid #3b82f6; background-color: #e6f7ff; }
    .mrp-border { border-top: 5px solid #10b981; background-color: #f6ffed; }
    .cad-border { border-top: 5px solid #f59e0b; background-color: #fffbe6; }
    .ua-border { border-top: 5px solid #8b5cf6; background-color: #f9f0ff; }
    .vanbree-border { border-top: 5px solid #06b6d4; background-color: #e6fffb; }
    .total-border { border-top: 5px solid #64748b; background-color: #f8fafc; }
    
    .stTabs [data-baseweb="tab"] { font-weight: 700; font-size: 16px; padding: 10px 20px; }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন ---
@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)
def get_data():
    client = get_gspread_client()
    sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    spreadsheet = client.open_by_key(sheet_id)
    df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
    
    df.columns = [c.strip() for c in df.columns]
    df['date'] = pd.to_datetime(df['date'], errors='coerce').dt.date
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    
    for col in ['Product', 'Job Type', 'Name', 'Team', 'Shift']:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()
    return df

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ন্যাভিগেশন ও ফিল্টার ---
    st.sidebar.markdown("# 🧭 Navigation")
    view_mode = st.sidebar.radio("Go to", ["📊 Dashboard", "🔍 Tracking System"])
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("# ⚙️ Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_selected = st.sidebar.selectbox("Team Name", ["All"] + sorted(df_raw['Team'].unique().tolist()))
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
    product_filter = st.sidebar.selectbox("Product Filter", ["All"] + sorted(df_raw['Product'].unique().tolist()))

    # ডাটা ফিল্টারিং
    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_filter != "All": mask &= (df_raw['Product'] == product_filter)
    df = df_raw[mask].copy()

    # মেইন ক্যালকুলেশন
    def get_avg(target_df, product_name, is_rework=False):
        temp = target_df[target_df['Product'].str.lower() == product_name.lower()]
        if is_rework:
            temp = temp[temp['Job Type'].str.lower() == 'rework']
        else:
            temp = temp[temp['Job Type'].str.lower() != 'rework']
        if temp.empty: return 0.0
        man_days = temp.groupby(['Name', 'date']).size().shape[0]
        return round(len(temp) / man_days, 2) if man_days > 0 else 0.0

    if view_mode == "📊 Dashboard":
        st.markdown("<h1 style='text-align: center;'>Performance Analytics</h1>", unsafe_allow_html=True)
        
        # কার্ড সেকশন
        c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
        with c1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2 style="color:#ef4444;">{get_avg(df, "Floorplan Queue", True)}</h2></div>', unsafe_allow_html=True)
        with c2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2 style="color:#3b82f6;">{get_avg(df, "Floorplan Queue")}</h2></div>', unsafe_allow_html=True)
        with c3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2 style="color:#10b981;">{get_avg(df, "Measurement Queue")}</h2></div>', unsafe_allow_html=True)
        with c4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2 style="color:#f59e0b;">{get_avg(df, "Autocad Queue")}</h2></div>', unsafe_allow_html=True)
        with c5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2 style="color:#8b5cf6;">0.0</h2></div>', unsafe_allow_html=True)
        with c6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2 style="color:#06b6d4;">0.0</h2></div>', unsafe_allow_html=True)
        with c7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2 style="color:#64748b;">{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📉 Overview & Trend", "👥 Team Summary", "🎨 Artist Analysis"])

        with tab1:
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                st.subheader("Daily Productivity Trend")
                trend_df = df.groupby('date').size().reset_index(name='Orders')
                fig_trend = px.line(trend_df, x='date', y='Orders', markers=True, height=400)
                st.plotly_chart(fig_trend, use_container_width=True)
            with col_t2:
                st.subheader("🏆 Leaderboard")
                leader_df = df.groupby('Name').size().reset_index(name='Orders').sort_values('Orders', ascending=False).head(5)
                for i, row in enumerate(leader_df.itertuples(), 1):
                    st.info(f"{i}. **{row.Name}** - {row.Orders} Orders")

        with tab2:
            st.subheader("Detailed Team Performance")
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'),
                Rework=('Job Type', lambda x: x.str.lower().eq('rework').sum()),
                FP=('Product', lambda x: x.str.lower().eq('floorplan queue').sum()),
                Orders=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                SQM=('SQM', 'sum')
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            
            st.subheader("Performance Breakdown Section (Artist Summary)")
            art_sum = df.groupby(['Name', 'Team', 'Shift']).agg(
                Order=('Ticket ID', 'count'),
                Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: x.str.lower().eq('rework').sum()),
                FP=('Product', lambda x: x.str.lower().eq('floorplan queue').sum()),
                MRP=('Product', lambda x: x.str.lower().eq('measurement queue').sum()),
                SQM=('SQM', 'sum'),
                Days=('date', 'nunique')
            ).reset_index()
            art_sum['Idle'] = (art_sum['Days'] * 400) - art_sum['Time']
            art_sum['Idle'] = art_sum['Idle'].apply(lambda x: max(0, int(x)))
            st.dataframe(art_sum.sort_values('Order', ascending=False), use_container_width=True, hide_index=True)

        with tab3:
            artist_list = sorted(df['Name'].unique().tolist())
            artist_selected = st.selectbox("Select Artist for Details", artist_list)
            artist_df = df[df['Name'] == artist_selected]
            
            c_a1, c_a2 = st.columns([1, 1.5])
            with c_a1:
                st.subheader(f"Stats: {artist_selected}")
                proj_counts = artist_df.groupby('Product').size().reset_index(name='Unique Orders')
                fig_art = px.bar(proj_counts, x='Product', y='Unique Orders', text='Unique Orders', color='Product', height=400)
                fig_art.update_traces(textposition='outside')
                st.plotly_chart(fig_art, use_container_width=True)
            with c_a2:
                st.subheader("Performance Detail Log")
                st.dataframe(artist_df[['date', 'Ticket ID', 'Product', 'SQM', 'Time']], use_container_width=True, hide_index=True)

    elif view_mode == "🔍 Tracking System":
        st.title("🎯 Performance Tracking")
        st.warning("Tracking logic under development based on criteria.")
        st.dataframe(df, use_container_width=True)

except Exception as e:
    st.error(f"Error connecting to data: {e}")
