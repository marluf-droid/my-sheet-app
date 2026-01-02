import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ---
st.set_page_config(page_title="Performance Analytics", layout="wide")

# আধুনিক স্মার্ট ডিজাইন (সব আইকন রিমুভড)
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
    creds_info = json.loads(st.secrets["JSON_KEY"])
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=600)
def load_all_data():
    client = get_gspread_client()
    master_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
    efficiency_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE"

    # মাস্টার এবং ইয়ারলি শিট লোড
    df_m = pd.DataFrame(client.open_by_key(master_id).worksheet("DATA").get_all_records())
    df_y = pd.DataFrame(client.open_by_key(efficiency_id).worksheet("FINAL SUMMARY").get_all_records())

    # কলাম ক্লিন করা
    df_m.columns = [c.strip() for c in df_m.columns]
    df_y.columns = [c.strip() for c in df_y.columns]
    
    # ডাটা টাইপ ঠিক করা
    df_m['date'] = pd.to_datetime(df_m['date'], errors='coerce').dt.date
    df_m['Time'] = pd.to_numeric(df_m['Time'], errors='coerce').fillna(0)
    df_m['SQM'] = pd.to_numeric(df_m['SQM'], errors='coerce').fillna(0)
    
    # টেক্সট কলাম ক্লিন করা
    text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
    for col in text_cols:
        if col in df_m.columns: df_m[col] = df_m[col].astype(str).str.strip()
    
    return df_m, df_y

try:
    df_master, df_yearly = load_all_data()

    # --- ৩. ন্যাভিগেশন ---
    st.sidebar.title("Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Yearly Artist Profile", "Tracking System"])
    st.sidebar.markdown("---")
    
    st.sidebar.title("Global Filters")
    start_date = st.sidebar.date_input("Start Date", df_master['date'].min())
    end_date = st.sidebar.date_input("End Date", df_master['date'].max())
    
    # গ্লোবাল ফিল্টার অনুযায়ী ডাটা
    mask = (df_master['date'] >= start_date) & (df_master['date'] <= end_date)
    team_list = ["All"] + sorted(df_master['Team'].unique().tolist())
    team_selected = st.sidebar.selectbox("Team Name", team_list)
    if team_selected != "All": mask &= (df_master['Team'] == team_selected)
    
    df = df_master[mask].copy()

    # ম্যান-ডে ক্যালকুলেশন লজিক
    def get_man_day_avg(target_df, p_name, j_type="Live Job"):
        subset = target_df[(target_df['Product'] == p_name) & (target_df['Job Type'] == j_type)]
        if subset.empty: return 0.0
        man_days = subset.groupby(['Name', 'date']).size().shape[0]
        return round(len(subset) / man_days, 2)

    # --- ৪. ড্যাশবোর্ড পেজ ---
    if page == "Dashboard":
        st.markdown("<h2 style='text-align: center;'>Performance Analytics 2025</h2>", unsafe_allow_html=True)
        
        # ৭টি গ্লোবাল কার্ডস
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{get_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{get_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{get_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{get_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree AVG<br><h2>{get_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        tab_team, tab_artist = st.tabs(["👥 Team Summary", "🎨 Individual Analysis"])

        with tab_team:
            # --- টিম সামারি (সব কলাম ফিরিয়ে আনা হয়েছে) ---
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
            # --- আর্টিস্ট সামারি (ইউনিক আর্টিস্ট) ---
            st.subheader("Performance Breakdown Section (Artist Summary)")
            artist_brk = df.groupby(['Name', 'Team', 'Shift']).agg(
                Order=('Ticket ID', 'count'), Time=('Time', 'sum'),
                Rework=('Job Type', lambda x: (x == 'Rework').sum()),
                FP=('Product', lambda x: (x == 'Floorplan Queue').sum()),
                MRP=('Product', lambda x: (x == 'Measurement Queue').sum()),
                UA=('Product', lambda x: (x == 'Urban Angles').sum()),
                CAD=('Product', lambda x: (x == 'Autocad Queue').sum()),
                VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()),
                SQM=('SQM', 'sum'), days=('date', 'nunique')
            ).reset_index()
            # Idle Time Logic
            artist_brk['Idle'] = (artist_brk['days'] * 400) - artist_brk['Time']
            artist_brk['Idle'] = artist_brk['Idle'].apply(lambda x: max(0, x))
            
            final_breakdown_cols = ['Name', 'Team', 'Shift', 'Order', 'Time', 'Idle', 'Rework', 'FP', 'MRP', 'UA', 'CAD', 'VanBree', 'SQM']
            st.dataframe(artist_brk[final_breakdown_cols].sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=600)

        with tab_artist:
            # ইন্ডিভিজুয়াল এনালাইসিস
            u_names = sorted(df['Name'].unique().tolist())
            a_sel = st.selectbox("Select Artist for Details", u_names)
            a_df = df[df['Name'] == a_sel]
            
            st.subheader(f"Insights: {a_sel}")
            p1, p2, p3, p4, p5, p6, p7 = st.columns(7)
            with p1: st.markdown(f'<div class="metric-card rework-border">Personal Rework<br><h2>{calculate_man_day_avg(a_df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
            with p2: st.markdown(f'<div class="metric-card fp-border">Personal FP<br><h2>{calculate_man_day_avg(a_df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p3: st.markdown(f'<div class="metric-card mrp-border">Personal MRP<br><h2>{calculate_man_day_avg(a_df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p4: st.markdown(f'<div class="metric-card cad-border">Personal CAD<br><h2>{calculate_man_day_avg(a_df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p5: st.markdown(f'<div class="metric-card ua-border">Personal UA<br><h2>{calculate_man_day_avg(a_df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p6: st.markdown(f'<div class="metric-card vanbree-border">Personal Van Bree<br><h2>{calculate_man_day_avg(a_df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
            with p7: st.markdown(f'<div class="metric-card total-border">Total Jobs<br><h2>{len(a_df)}</h2></div>', unsafe_allow_html=True)

            col_a1, col_a2 = st.columns([1, 1])
            with col_a1:
                st.subheader("Job Distribution")
                p_data = a_df['Product'].value_counts().reset_index()
                p_data.columns = ['Product', 'Orders']
                fig_bar = px.bar(p_data, x='Product', y='Orders', text='Orders', color='Product', color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_bar.update_traces(textposition='outside', cliponaxis=False)
                st.plotly_chart(fig_bar, use_container_width=True)
            with col_a2:
                # Efficiency Chart ফিরিয়ে আনা হয়েছে
                st.subheader("Efficiency (Time vs SQM)")
                fig_scat = px.scatter(a_df, x="SQM", y="Time", size="Time", color="Product", hover_data=['Ticket ID'], size_max=40)
                st.plotly_chart(fig_scat, use_container_width=True)

            st.markdown("---")
            st.subheader("Activity Log (Click Link to open RT)")
            log_df = a_df.copy()
            log_df['date'] = log_df['date'].apply(lambda x: x.strftime('%m/%d/%Y'))
            log_df['RT Link'] = log_df['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
            st.dataframe(log_df[['date', 'Ticket ID', 'RT Link', 'Product', 'SQM', 'Time']], column_config={"RT Link": st.column_config.LinkColumn("View")}, use_container_width=True, hide_index=True)

    # --- ৫. ইয়ারলি প্রোফাইল পেজ (আপনার দেওয়া নতুন রিকোয়ারমেন্ট) ---
    elif page == "Yearly Artist Profile":
        st.markdown("<h2 style='text-align: center;'>Artist Yearly Performance Summary</h2>", unsafe_allow_html=True)
        
        all_artist_y = sorted(df_yearly['USER NAME ALL'].unique().tolist())
        a_y_sel = st.selectbox("Search Artist Profile", all_artist_y)
        y_data = df_yearly[df_yearly['USER NAME ALL'] == a_y_sel]
        
        if not y_data.empty:
            # সারা বছরের তথ্য সামারি করা হচ্ছে
            total_fp = y_data['FLOOR PLAN'].sum()
            total_mrp = y_data['MEASUREMENT'].sum()
            avg_time = round(y_data['AVG TIME'].mean(), 1)
            total_days = y_data['WORKING DAY'].sum()
            
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Annual FP Done", int(total_fp))
            c2.metric("Annual MRP Done", int(total_mrp))
            c3.metric("Annual Avg Time", f"{avg_time}m")
            c4.metric("Total Active Days", int(total_days))
            
            st.markdown("---")
            st.subheader("Monthly Productivity Breakdown")
            # আপনার শিটের মতো মান্থলি টেবিল
            display_cols = ['Month', 'LIVE ORDER', 'FLOOR PLAN', 'MEASUREMENT', 'AUTO CAD', 'URBAN ANGLES', 'VanBree Media', 'AVG TIME', 'WORKING DAY']
            st.dataframe(y_data[display_cols], use_container_width=True, hide_index=True)
            
            # ট্রেন্ড গ্রাফ
            trend_fig = px.bar(y_data, x='Month', y=['FLOOR PLAN', 'MEASUREMENT', 'AUTO CAD'], barmode='group', title="Month-wise Performance")
            st.plotly_chart(trend_fig, use_container_width=True)
        else:
            st.info("No yearly data found for this artist.")

    # --- ৬. ট্র্যাকিং সিস্টেম ---
    elif page == "Tracking System":
        st.title("Performance Tracking")
        tdf = df.copy()
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        st.dataframe(tdf, column_config={"RT Link": st.column_config.LinkColumn("Open RT")}, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
