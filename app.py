import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ও ডিজাইন ---
st.set_page_config(page_title="Performance Analytics Pro", layout="wide")

st.markdown("""
    <style>
    .metric-card { 
        padding: 15px; border-radius: 12px; text-align: center; color: #1e293b; 
        background: #ffffff; border-top: 5px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }
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
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_all_data():
    client = get_gspread_client()
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    df_m = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_y = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    df_m.columns = [c.strip() for c in df_m.columns]
    df_y.columns = [c.strip() for c in df_y.columns]
    
    df_m['date'] = pd.to_datetime(df_m['date'], errors='coerce').dt.date
    numeric_cols = ['Time', 'SQM', 'FLOOR PLAN', 'MEASUREMENT', 'AUTO CAD', 'URBAN ANGLES', 'VanBree Media', 'WORKING DAY', 'AVG TIME', 'LIVE ORDER']
    
    for df in [df_m, df_y]:
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    
    return df_m, df_y

try:
    df_master, df_yearly = load_all_data()

    # --- ৩. সাইডবার ন্যাভিগেশন ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Dashboard Mode", ["Live Dashboard", "Yearly Artist Profile", "Tracking System"])
    st.sidebar.markdown("---")
    
    st.sidebar.title("Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_master['date'].min())
    end_date = st.sidebar.date_input("End Date", df_master['date'].max())
    
    df = df_master[(df_master['date'] >= start_date) & (df_master['date'] <= end_date)].copy()

    def get_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৪. পেজ ১: লাইভ ড্যাশবোর্ড ---
    if page == "Live Dashboard":
        st.markdown("<h2 style='text-align: center;'>Live Performance Dashboard</h2>", unsafe_allow_html=True)
        
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2>{get_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Orders<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        tab1, tab2 = st.tabs(["Team Summary", "Individual Analysis"])

        with tab1:
            st.subheader("Detailed Team Performance")
            team_sum = df.groupby(['Team', 'Shift']).agg(Artists=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Time=('Time', 'sum'), FP=('Product', lambda x: (x == 'Floorplan Queue').sum())).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)

        with tab2:
            st.subheader("Artist Insights")
            a_sel = st.selectbox("Select Artist", sorted(df['Name'].unique()))
            a_df = df[df['Name'] == a_sel]
            
            p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
            with p1: st.markdown(f'<div class="metric-card rework-border">Personal Rework<br><h2>{get_man_day_avg(a_df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
            with p2: st.markdown(f'<div class="metric-card fp-border">Personal FP<br><h2>{get_man_day_avg(a_df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p3: st.markdown(f'<div class="metric-card mrp-border">Personal MRP<br><h2>{get_man_day_avg(a_df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p7: st.markdown(f'<div class="metric-card total-border">Total Jobs<br><h2>{len(a_df)}</h2></div>', unsafe_allow_html=True)

            c_a1, c_a2 = st.columns([1, 1.5])
            with c_a1:
                st.plotly_chart(px.bar(a_df['Product'].value_counts().reset_index(), x='Product', y='count', text='count', title="Job Count"), use_container_width=True)
            with c_a2:
                st.plotly_chart(px.scatter(a_df, x="SQM", y="Time", color="Product", size="Time", hover_data=['Ticket ID'], title="Efficiency (Time vs SQM)"), use_container_width=True)

    # --- ৫. পেজ ২: Yearly Artist Profile (আপনার ৫ নম্বর ছবির মতো) ---
    elif page == "Yearly Artist Profile":
        st.markdown("<h2 style='text-align: center;'>Yearly Performance Profile</h2>", unsafe_allow_html=True)
        
        all_artist_y = sorted(df_yearly['USER NAME ALL'].unique())
        artist_y = st.selectbox("Search Artist Profile", all_artist_y)
        
        # ওই আর্টিস্টের সব মাসের ডাটা ফিল্টার করা
        y_data_all = df_yearly[df_yearly['USER NAME ALL'] == artist_y]
        
        if not y_data_all.empty:
            # সারা বছরের মোট হিসাব (Aggregated)
            total_fp = y_data_all['FLOOR PLAN'].sum()
            total_mrp = y_data_all['MEASUREMENT'].sum()
            avg_time_yearly = round(y_data_all['AVG TIME'].mean(), 1)
            total_working_days = y_data_all['WORKING DAY'].sum()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Annual Total FP", int(total_fp))
            c2.metric("Annual Total MRP", int(total_mrp))
            c3.metric("Annual Avg Time", f"{avg_time_yearly}m")
            c4.metric("Total Active Days", int(total_working_days))
            
            st.markdown("---")
            
            # আপনার শিটের মতো মান্থলি ব্রেকডাউন টেবিল
            st.subheader("Monthly Breakdown Table")
            display_cols = ['Month', 'LIVE ORDER', 'FLOOR PLAN', 'MEASUREMENT', 'AUTO CAD', 'URBAN ANGLES', 'VanBree Media', 'AVG TIME', 'WORKING DAY']
            st.dataframe(y_data_all[display_cols], use_container_width=True, hide_index=True)
            
            # ট্রেন্ড চার্ট
            st.subheader("Productivity Trend by Month")
            trend_fig = px.bar(y_data_all, x='Month', y=['FLOOR PLAN', 'MEASUREMENT', 'AUTO CAD'], barmode='group', title="Orders Per Month")
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.warning("No yearly data found.")

    # --- ৬. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("Performance Tracking")
        tdf = df.copy()
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        st.dataframe(tdf, column_config={"RT Link": st.column_config.LinkColumn("Open")}, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
