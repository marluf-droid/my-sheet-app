import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
import json

# --- ১. পেজ সেটিংস ও স্মার্ট ডিজাইন (আইকন পুরোপুরি হাইড করার লজিক) ---
st.set_page_config(page_title="Performance Analytics 2025", layout="wide")

st.markdown("""
    <style>
    /* মেনু, হেডার এবং GitHub আইকন হাইড করা */
    #MainMenu {visibility: hidden;}
    header {visibility: hidden;}
    footer {visibility: hidden;}
    div[data-testid="stToolbar"] {visibility: hidden; display: none !important;}
    div[data-testid="stDecoration"] {display: none !important;}
    .stDeployButton {display:none !important;}
    
    /* আধুনিক ফন্ট এবং মেট্রিক কার্ড ডিজাইন */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }

    .metric-card {
        padding: 15px; border-radius: 12px; text-align: center; color: #1e293b;
        background: #ffffff; border: 1px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
        margin-bottom: 10px;
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

# এভারেজ ক্যালকুলেশন ফাংশন
def calculate_avg(target_df, product_name, is_rework=False):
    temp = target_df[target_df['Product'].str.lower() == product_name.lower()]
    if is_rework:
        temp = temp[temp['Job Type'].str.lower() == 'rework']
    else:
        temp = temp[temp['Job Type'].str.lower() != 'rework']
    
    if temp.empty: return 0.0
    man_days = temp.groupby(['Name', 'date']).size().shape[0]
    return round(len(temp) / man_days, 2) if man_days > 0 else 0.0

try:
    df_raw = get_data()

    # --- ৩. সাইডবার ফিল্টার ---
    st.sidebar.markdown("# ⚙️ Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_selected = st.sidebar.selectbox("Team Name", ["All"] + sorted(df_raw['Team'].unique().tolist()))
    shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
    emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
    product_filter = st.sidebar.selectbox("Product Filter", ["All"] + sorted(df_raw['Product'].unique().tolist()))

    mask = (df_raw['date'] >= start_date) & (df_raw['date'] <= end_date)
    if team_selected != "All": mask &= (df_raw['Team'] == team_selected)
    if shift_selected != "All": mask &= (df_raw['Shift'] == shift_selected)
    if emp_type_selected != "All": mask &= (df_raw['Employee Type'] == emp_type_selected)
    if product_filter != "All": mask &= (df_raw['Product'] == product_filter)
    df = df_raw[mask].copy()

    # --- ৪. মেইন ড্যাশবোর্ড ---
    st.markdown("<h1 style='text-align: center;'>Performance Analytics 2025</h1>", unsafe_allow_html=True)
    
    # টপ কার্ডস (Global View)
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)
    with c1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2 style="color:#ef4444;">{calculate_avg(df, "Floorplan Queue", True)}</h2></div>', unsafe_allow_html=True)
    with c2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2 style="color:#3b82f6;">{calculate_avg(df, "Floorplan Queue")}</h2></div>', unsafe_allow_html=True)
    with c3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2 style="color:#10b981;">{calculate_avg(df, "Measurement Queue")}</h2></div>', unsafe_allow_html=True)
    with c4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2 style="color:#f59e0b;">{calculate_avg(df, "Autocad Queue")}</h2></div>', unsafe_allow_html=True)
    with c5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2 style="color:#8b5cf6;">{calculate_avg(df, "Urban Angles")}</h2></div>', unsafe_allow_html=True)
    with c6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2 style="color:#06b6d4;">{calculate_avg(df, "Van Bree Media")}</h2></div>', unsafe_allow_html=True)
    with c7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2 style="color:#64748b;">{len(df)}</h2></div>', unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📉 Overview & Trend", "👥 Team Summary", "🎨 Artist Analysis"])

    # --- ট্যাব ১: ট্রেন্ড ও লিডারবোর্ড ---
    with tab1:
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            st.subheader("Daily Productivity Trend")
            trend_df = df.groupby('date').size().reset_index(name='Orders')
            st.plotly_chart(px.line(trend_df, x='date', y='Orders', markers=True, height=400), use_container_width=True)
        with col_t2:
            st.subheader("🏆 Leaderboard")
            leader_df = df.groupby('Name').size().reset_index(name='Orders').sort_values('Orders', ascending=False).head(5)
            for i, row in enumerate(leader_df.itertuples(), 1):
                st.info(f"{i}. **{row.Name}** - {row.Orders} Orders")

    # --- ট্যাব ২: টিম সামারি (সব কলামসহ) ---
    with tab2:
        st.subheader("Detailed Team Performance")
        # টিম সামারিতে সব প্রোডাক্টের ব্রেকডাউন যোগ করা হয়েছে
        team_sum = df.groupby(['Team', 'Shift']).agg(
            Present=('Name', 'nunique'),
            Rework=('Job Type', lambda x: x.str.lower().eq('rework').sum()),
            FP=('Product', lambda x: x.str.lower().eq('floorplan queue').sum()),
            MRP=('Product', lambda x: x.str.lower().eq('measurement queue').sum()),
            CAD=('Product', lambda x: x.str.lower().eq('autocad queue').sum()),
            UA=('Product', lambda x: x.str.lower().eq('urban angles').sum()),
            VanBree=('Product', lambda x: x.str.lower().eq('van bree media').sum()),
            Orders=('Ticket ID', 'count'),
            Time=('Time', 'sum'),
            SQM=('SQM', 'sum')
        ).reset_index()
        st.dataframe(team_sum, use_container_width=True, hide_index=True)
        
        st.subheader("Performance Breakdown Section (Artist Summary)")
        art_sum = df.groupby(['Name', 'Team', 'Shift']).agg(
            Order=('Ticket ID', 'count'),
            Time=('Time', 'sum'),
            Days=('date', 'nunique'),
            Rework=('Job Type', lambda x: x.str.lower().eq('rework').sum()),
            FP=('Product', lambda x: x.str.lower().eq('floorplan queue').sum()),
            MRP=('Product', lambda x: x.str.lower().eq('measurement queue').sum()),
            CAD=('Product', lambda x: x.str.lower().eq('autocad queue').sum()),
            UA=('Product', lambda x: x.str.lower().eq('urban angles').sum()),
            VanBree=('Product', lambda x: x.str.lower().eq('van bree media').sum()),
            SQM=('SQM', 'sum')
        ).reset_index()
        art_sum['Idle'] = (art_sum['Days'] * 400) - art_sum['Time']
        art_sum['Idle'] = art_sum['Idle'].apply(lambda x: max(0, int(x)))
        st.dataframe(art_sum.sort_values('Order', ascending=False), use_container_width=True, hide_index=True)

    # --- ট্যাব ৩: আর্টিস্ট অ্যানালাইসিস (পার্সোনাল কার্ডস ও চার্ট) ---
    with tab3:
        artist_selected = st.selectbox("Select Artist for Details", sorted(df['Name'].unique().tolist()))
        artist_df = df[df['Name'] == artist_selected].copy()
        
        if not artist_df.empty:
            st.markdown(f"### 🎯 Personal Performance: {artist_selected}")
            
            # আর্টিস্টের পার্সোনাল সব এভারেজ কার্ডস
            ca1, ca2, ca3, ca4, ca5, ca6, ca7 = st.columns(7)
            with ca1: st.markdown(f'<div class="metric-card rework-border">Personal Rework<br><h3>{calculate_avg(artist_df, "Floorplan Queue", True)}</h3></div>', unsafe_allow_html=True)
            with ca2: st.markdown(f'<div class="metric-card fp-border">Personal FP<br><h3>{calculate_avg(artist_df, "Floorplan Queue")}</h3></div>', unsafe_allow_html=True)
            with ca3: st.markdown(f'<div class="metric-card mrp-border">Personal MRP<br><h3>{calculate_avg(artist_df, "Measurement Queue")}</h3></div>', unsafe_allow_html=True)
            with ca4: st.markdown(f'<div class="metric-card cad-border">Personal CAD<br><h3>{calculate_avg(artist_df, "Autocad Queue")}</h3></div>', unsafe_allow_html=True)
            with ca5: st.markdown(f'<div class="metric-card ua-border">Personal UA<br><h3>{calculate_avg(artist_df, "Urban Angles")}</h3></div>', unsafe_allow_html=True)
            with ca6: st.markdown(f'<div class="metric-card total-border">Total Jobs<br><h3>{len(artist_df)}</h3></div>', unsafe_allow_html=True)
            with ca7: st.markdown(f'<div class="metric-card vanbree-border">Avg Time/Job<br><h3>{round(artist_df["Time"].mean(),1)}m</h3></div>', unsafe_allow_html=True)

            col_c1, col_c2 = st.columns([1, 1])
            with col_c1:
                st.subheader("Project Distribution")
                proj_counts = artist_df.groupby('Product').size().reset_index(name='Orders')
                fig_bar = px.bar(proj_counts, x='Product', y='Orders', text='Orders', color='Product', height=400)
                fig_bar.update_traces(textposition='outside')
                st.plotly_chart(fig_bar, use_container_width=True)
            
            with col_c2:
                st.subheader("Efficiency: Time vs SQM")
                # এটি দেখায় যে আর্টিস্ট ছোট SQM-এর কাজে বেশি সময় নিচ্ছে কি না
                fig_scatter = px.scatter(artist_df, x='SQM', y='Time', color='Product', hover_data=['Ticket ID', 'date'], height=400)
                st.plotly_chart(fig_scatter, use_container_width=True)

            st.subheader("Performance Detail Log")
            st.dataframe(artist_df[['date', 'Ticket ID', 'Product', 'SQM', 'Time']].sort_values('date', ascending=False), use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Something went wrong: {e}")
