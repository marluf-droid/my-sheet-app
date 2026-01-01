import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ও স্মার্ট ডিজাইন ---
st.set_page_config(page_title="Performance Analytics", layout="wide")

# আধুনিক ক্লিন CSS (সার্কেল আইকন রিমুভ করা হয়েছে)
st.markdown("""
    <style>
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
    st.sidebar.markdown("## 🧭 Navigation")
    page = st.sidebar.radio("Go to", ["📊 Dashboard", "🔍 Tracking System"])
    st.sidebar.markdown("---")
    
    st.sidebar.markdown("## ⚙️ Global Filters")
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

    # --- ৪. স্পেশাল ক্যালকুলেশন ---
    def calculate_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        total_tasks = len(subset)
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(total_tasks / man_days, 2) if man_days > 0 else 0.0

    # --- ৫. মেইন ড্যাশবোর্ড ---
    if "Dashboard" in page:
        st.markdown("<h2 style='text-align: center; color: #0f172a;'>Performance Analytics</h2>", unsafe_allow_html=True)
        
        # কার্ড মেট্রিক্স (আইকন ছাড়া ক্লিন ডিজাইন)
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2 style="color:#ef4444">{calculate_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2 style="color:#3b82f6">{calculate_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2 style="color:#10b981">{calculate_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2 style="color:#f59e0b">{calculate_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2 style="color:#8b5cf6">{calculate_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree<br><h2 style="color:#06b6d4">{calculate_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2 style="color:#64748b">{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        
        tab1, tab2, tab3 = st.tabs(["📉 Overview & Trend", "👥 Team & Artist Summary", "🎨 Artist Analysis"])

        with tab1:
            col_t1, col_t2 = st.columns([2, 1])
            with col_t1:
                st.subheader("Daily Productivity Trend")
                trend_df = df.groupby('date').size().reset_index(name='Orders')
                fig_trend = px.line(trend_df, x='date', y='Orders', markers=True, color_discrete_sequence=['#3b82f6'])
                st.plotly_chart(fig_trend, use_container_width=True)
            with col_t2:
                st.subheader("🏆 Leaderboard")
                tops = df.groupby('Name').size().sort_values(ascending=False).head(5)
                for i, (name, count) in enumerate(tops.items()):
                    st.info(f"{i+1}. **{name}** - {count} Orders")

        with tab2:
            # --- ৫.১ TEAM SUMMARY ---
            st.subheader("Detailed Team Performance")
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
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            
            st.markdown("---")
            # --- ৫.২ PERFORMANCE BREAKDOWN (এখন টিম সামারির নিচেই থাকবে) ---
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
            
            artist_breakdown['Idle'] = (artist_breakdown['worked_days'] * 400) - artist_breakdown['Time']
            artist_breakdown['Idle'] = artist_breakdown['Idle'].apply(lambda x: max(0, x))
            
            artist_breakdown = artist_breakdown.sort_values(by='Order', ascending=False)
            break_cols = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'VanBree', 'SQM']
            st.dataframe(artist_breakdown[break_cols], use_container_width=True, hide_index=True)

      with tab3:
            # ১. আর্টিস্ট সিলেকশন
            u_names = sorted(df['Name'].unique().tolist())
            top_nm = artist_breakdown['Name'].iloc[0] if not artist_breakdown.empty else ""
            a_sel = st.selectbox("Select Artist for Details", u_names, index=u_names.index(top_nm) if top_nm in u_names else 0)
            
            # ওই নির্দিষ্ট আর্টিস্টের ডাটা ফিল্টার
            a_df = df[df['Name'] == a_sel]

            # ২. আর্টিস্ট স্পেসিফিক কার্ড মেট্রিক্স (আগের জেনারেল কার্ডের বদলে এখানে শুধু ওই আর্টিস্টের ডাটা)
            st.markdown(f"### 📊 Individual Performance: {a_sel}")
            ma1, ma2, ma3, ma4, ma5, ma6 = st.columns(6)
            with ma1: st.metric("Rework AVG", calculate_man_day_avg(a_df, "Floorplan Queue", "Rework"))
            with ma2: st.metric("FP AVG", calculate_man_day_avg(a_df, "Floorplan Queue", "Live Job"))
            with ma3: st.metric("MRP AVG", calculate_man_day_avg(a_df, "Measurement Queue", "Live Job"))
            with ma4: st.metric("CAD AVG", calculate_man_day_avg(a_df, "Autocad Queue", "Live Job"))
            with ma5: st.metric("Total SQM", round(a_df['SQM'].sum(), 2))
            with ma6: st.metric("Total Orders", len(a_df))

            st.markdown("---")

            # ৩. চার্ট সেকশন (এক সারিতে দুটি চার্ট)
            col_chart1, col_chart2 = st.columns(2)

            with col_chart1:
                st.subheader("Product Distribution")
                p_data = a_df['Product'].value_counts().reset_index()
                p_data.columns = ['Product', 'Unique Orders']
                fig_bar = px.bar(p_data, x='Product', y='Unique Orders', text='Unique Orders', 
                                 color='Product', color_discrete_sequence=px.colors.qualitative.Set3)
                fig_bar.update_layout(showlegend=False, height=400)
                st.plotly_chart(fig_bar, use_container_width=True)

            with col_chart2:
                st.subheader("Efficiency: SQM vs Time")
                # SQM এবং Time এর রিলেশন দেখানোর জন্য স্ক্যাটার চার্ট
                fig_scatter = px.scatter(a_df, x='SQM', y='Time', color='Product',
                                         hover_data=['Ticket ID', 'date'],
                                         trendline="ols", # ট্রেন্ডলাইন অপশনাল, ডাটা বেশি হলে ভালো দেখায়
                                         title="Time spent based on SQM size")
                fig_scatter.update_layout(height=400)
                st.plotly_chart(fig_scatter, use_container_width=True)

            # ৪. ডেইলি প্রোডাক্টিভিটি ট্রেন্ড (আর্টিস্টের জন্য আলাদা)
            st.subheader(f"Daily Productivity Trend of {a_sel}")
            a_trend = a_df.groupby('date').size().reset_index(name='Orders')
            fig_a_trend = px.area(a_trend, x='date', y='Orders', markers=True, 
                                  line_shape='spline', color_discrete_sequence=['#10b981'])
            fig_a_trend.update_layout(height=300)
            st.plotly_chart(fig_a_trend, use_container_width=True)

            # ৫. পারফরম্যান্স লগ (নিচের সারিতে)
            st.markdown("---")
            st.subheader("📋 Performance Detail Log")
            log_df = a_df.copy()
            log_df['date'] = log_df['date'].apply(lambda x: x.strftime('%m/%d/%Y'))
            # এফিসিয়েন্সি কলাম যোগ করা (Time/SQM)
            log_df['Time/SQM'] = (log_df['Time'] / log_df['SQM']).replace([float('inf'), -float('inf')], 0).round(2)
            
            detail_cols = ['date', 'Ticket ID', 'Product', 'SQM', 'Time', 'Time/SQM', 'Floor', 'Labels']
            st.dataframe(log_df[detail_cols].rename(columns={'date':'Date', 'Ticket ID':'Order ID'}), 
                         use_container_width=True, hide_index=True)

    # --- ৬. ট্র্যাকিং সিস্টেম ---
    elif "Tracking" in page:
        st.title("🎯 Tracking System")
        criteria = st.selectbox("Select Criteria", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        
        s_ip = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | ((tdf['Employee Type'] == 'Artist') & (((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) | (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10)))))
        s_mt = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | ((tdf['Employee Type'] == 'Artist') & ((tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40)))))
        h_ts = (tdf['Time'] > (tdf['SQM'] + 15)) & ~s_mt

        if criteria == "Short IP": tdf = tdf[s_ip]
        elif criteria == "Spending More Time": tdf = tdf[s_mt]
        elif criteria == "High Time vs SQM": tdf = tdf[h_ts]

        st.metric("Total Found", len(tdf))
        st.dataframe(tdf, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Something went wrong: {e}")

