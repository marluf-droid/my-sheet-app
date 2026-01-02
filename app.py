import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ---
st.set_page_config(page_title="Performance Analytics", layout="wide")

# ডিজাইন স্টাইল
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

    # --- ৩. সাইডবার ন্যাভিগেশন ---
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Tracking System"])
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("## Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
    end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
    
    team_list = ["All"] + sorted(df_raw['Team'].unique().tolist())
    team_selected = st.sidebar.selectbox("Team Name", team_list)
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

    def calculate_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        total_tasks = len(subset)
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৪. মেইন ড্যাশবোর্ড পেজ ---
    if page == "Dashboard":
        st.markdown("<h2 style='text-align: center;'>Performance Analytics 2025</h2>", unsafe_allow_html=True)
        
        # গ্লোবাল কার্ডস
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{calculate_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{calculate_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{calculate_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{calculate_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{calculate_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree AVG<br><h2>{calculate_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["Overview", "Team & Artist Summary", "Artist Analysis"])

        with tab1:
            col_trend, col_lb = st.columns([2, 1])
            with col_trend:
                st.subheader("Daily Productivity Trend")
                trend_df = df.groupby('date').size().reset_index(name='Orders')
                st.plotly_chart(px.line(trend_df, x='date', y='Orders', markers=True), use_container_width=True)
            with col_lb:
                st.subheader("Leaderboard")
                tops = df.groupby('Name').size().sort_values(ascending=False).head(5)
                for name, count in tops.items(): st.info(f"**{name}** - {count} Orders")

        with tab2:
            st.subheader("Detailed Team Performance")
            # আপনার সব কলাম পুনরায় যোগ করা হয়েছে
            team_sum = df.groupby(['Team', 'Shift']).agg(
                Present=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()), FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()), CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()), VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                SQM=('SQM', 'sum')
            ).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            st.subheader("Performance Breakdown Section (Artist Summary)")
            artist_brk = df.groupby(['Name', 'Team', 'Shift']).agg(Order=('Ticket ID', 'count'), Time=('Time', 'sum'), Rework=('Job Type', lambda x: (x == 'Rework').sum()), FP=('Product', lambda x: (x == 'Floorplan Queue').sum()), MRP=('Product', lambda x: (x == 'Measurement Queue').sum()), UA=('Product', lambda x: (x == 'Urban Angles').sum()), CAD=('Product', lambda x: (x == 'Autocad Queue').sum()), VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()), SQM=('SQM', 'sum'), days=('date', 'nunique')).reset_index()
            artist_brk['Idle'] = (artist_brk['days'] * 400) - artist_brk['Time']
            artist_brk['Idle'] = artist_brk['Idle'].apply(lambda x: max(0, x))
            st.dataframe(artist_brk.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=750)

        with tab3:
            u_names = sorted(df['Name'].unique().tolist())
            a_sel = st.selectbox("Select Artist for Analysis", u_names)
            a_df = df[df['Name'] == a_sel]
            
            st.subheader(f"Insights: {a_sel}")
            p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
            # আপনার চাহিদা মতো পার্সোনাল কার্ডস
            with p1: st.markdown(f'<div class="metric-card rework-border">Personal Rework<br><h2>{calculate_man_day_avg(a_df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
            with p2: st.markdown(f'<div class="metric-card fp-border">Personal FP<br><h2>{calculate_man_day_avg(a_df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p3: st.markdown(f'<div class="metric-card mrp-border">Personal MRP<br><h2>{calculate_man_day_avg(a_df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p4: st.markdown(f'<div class="metric-card cad-border">Personal CAD<br><h2>{calculate_man_day_avg(a_df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p5: st.markdown(f'<div class="metric-card ua-border">Personal UA<br><h2>{calculate_man_day_avg(a_df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p6: st.markdown(f'<div class="metric-card vanbree-border">Personal Van Bree<br><h2>{calculate_man_day_avg(a_df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p7: st.markdown(f'<div class="metric-card total-border">Total Jobs<br><h2>{len(a_df)}</h2></div>', unsafe_allow_html=True)

            col_a1, col_a2 = st.columns([1, 1])
            with col_a1:
                # বার চার্টে সব ভ্যালু যোগ করা হয়েছে
                st.subheader("Job Distribution")
                p_data = a_df['Product'].value_counts().reset_index()
                p_data.columns = ['Product', 'Orders']
                fig_bar = px.bar(p_data, x='Product', y='Orders', text='Orders', color='Product', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_bar.update_traces(textposition='outside', cliponaxis=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            with col_a2:
                st.subheader("Efficiency (Time vs SQM)")
                # হোভারে Ticket ID যোগ করা হয়েছে
                fig_scatter = px.scatter(a_df, x="SQM", y="Time", size="Time", color="Product", hover_data=['Ticket ID'], size_max=40)
                st.plotly_chart(fig_scatter, use_container_width=True)

            st.markdown("---")
            st.subheader("Activity Log (Click Link to open RT)")
            log_df = a_df.copy()
            log_df['RT Link'] = log_df['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
            # Ticket ID কলামের পাশেই লিঙ্ক বাটন
            st.dataframe(
                log_df[['date', 'Ticket ID', 'RT Link', 'Product', 'SQM', 'Floor', 'Labels', 'Time']],
                column_config={"RT Link": st.column_config.LinkColumn("View in RT", display_text="Open")},
                use_container_width=True, hide_index=True
            )

    elif page == "Tracking System":
        st.title("Performance Tracking")
        criteria = st.selectbox("Criteria", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        # অপ্রয়োজনীয় কলাম রিমুভ (পয়েন্ট ১)
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        
        s_mt = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | ((tdf['Employee Type'] == 'Artist') & ((tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40)))))
        if criteria == "Short IP": tdf = tdf[(((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | ((tdf['Employee Type'] == 'Artist') & (((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) | (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10)))))]
        elif criteria == "Spending More Time": tdf = tdf[s_mt]
        elif criteria == "High Time vs SQM": tdf = tdf[(tdf['Time'] > (tdf['SQM'] + 15)) & ~s_mt]
        
        st.metric("Total Jobs Found", len(tdf))
        # ট্র্যাকিং সিস্টেম এ Ticket ID এর ঠিক পাশেই RT Link (পয়েন্ট ৩)
        cols_to_show = ['Shift', 'Time', 'Ticket ID', 'RT Link', 'Name', 'date', 'Product', 'SQM', 'Floor', 'Labels', 'Job Type', 'Team']
        st.dataframe(tdf[cols_to_show], column_config={"RT Link": st.column_config.LinkColumn("RT", display_text="Open")}, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
