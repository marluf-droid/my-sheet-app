import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import plotly.express as px
from datetime import datetime
import json

# --- ১. পেজ সেটিংস ও স্মার্ট ডিজাইন ---
st.set_page_config(page_title="Performance Analytics", layout="wide")

# আধুনিক ক্লিন CSS (আপনার আগের স্টাইলটিই রাখা হয়েছে)
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
    
    .metric-card { 
        padding: 20px; border-radius: 12px; text-align: center; color: #1e293b; 
        background: #ffffff; border-top: 5px solid #e2e8f0;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05); 
    }
    .rework-border { border-top-color: #ef4444; background-color: #fff1f0; }
    .fp-border { border-top-color: #3b82f6; background-color: #e6f7ff; }
    .mrp-border { border-top-color: #10b981; background-color: #f6ffed; }
    .cad-border { border-top-color: #f59e0b; background-color: #fffbe6; }
    .ua-border { border-top-color: #8b5cf6; background-color: #f9f0ff; }
    .vanbree-border { border-top-color: #06b6d4; background-color: #e6fffb; }
    .total-border { border-top-color: #64748b; background-color: #f8fafc; }
    
    .stTabs [data-baseweb="tab"] { font-weight: 700; font-size: 16px; padding: 10px 20px; }
            .metric-box {
        padding: 10px; border-radius: 10px; text-align: center; margin-bottom: 10px;
        box-shadow: 2px 2px 5px rgba(0,0,0,0.05); border-left: 5px solid #ccc;
    }
    .cl-rework { background-color: #fee2e2; border-left-color: #ef4444; }
    .cl-fp { background-color: #e0f2fe; border-left-color: #3b82f6; }
    .cl-mrp { background-color: #dcfce7; border-left-color: #10b981; }
    .cl-cad { background-color: #fef9c3; border-left-color: #f59e0b; }
    .cl-ua { background-color: #f3e8ff; border-left-color: #8b5cf6; }
    .cl-vb { background-color: #ccfbf1; border-left-color: #06b6d4; }
    .cl-total { background-color: #f1f5f9; border-left-color: #64748b; }
    </style>
    """, unsafe_allow_html=True)

# --- ২. ডাটা কানেকশন ফাংশনস ---

@st.cache_resource
def get_gspread_client():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_info = json.loads(st.secrets["JSON_KEY"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_info, scope)
    return gspread.authorize(creds)

# জেনারেল ডাটা (Dashboard & Tracking এর জন্য)
@st.cache_data(ttl=600)
def get_data():
    client = get_gspread_client()
    sheet_id = "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y" # আপনার অরিজিনাল ডাটা শিট
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

# Monthly Summary ডাটা (আপনার নতুন Monthly Efficiency শিট থেকে)
@st.cache_data(ttl=600)
def get_summary_data():
    client = get_gspread_client()
    sheet_id = "1hFboFpRmst54yVUfESFAZE_UgNdBsaBAmHYA-9z5eJE" 
    spreadsheet = client.open_by_key(sheet_id)
    df_s = pd.DataFrame(spreadsheet.worksheet("FINAL SUMMARY").get_all_records())
    
    # কলামের নামগুলো ক্লিন করা (সব বড় হাতের এবং অতিরিক্ত স্পেস রিমুভ)
    df_s.columns = [" ".join(c.split()).upper() for c in df_s.columns]
    
    # কলাম কনভার্ট করা
    num_cols = [
        'FLOORPLAN', 'MEASUREMENT', 'AUTOCAD', 'URBAN ANGLES', 'VANBREEMEDIA', 'RE_WORK', 
        'LIVE ORDER', 'FP TIME', 'MRP TIME', 'CAD TIME', 'URBAN ANGLES TIME', 'RE_WORK TIME', 
        'WORKING TIME', 'AVG TIME', 'FP AVG', 'MRP AVG', 'CAD AVG', 'TUESDAY TO FRIDAY AVG', 'SATURDAY TO MONDAY'
    ]
    for col in num_cols:
        if col in df_s.columns:
            df_s[col] = pd.to_numeric(df_s[col], errors='coerce').fillna(0)
    return df_s

# --- ৩. মেইন অ্যাপ লজিক ---

try:
    # ন্যাভিগেশন
    st.sidebar.markdown("## Navigation")
    page = st.sidebar.radio("Go to", ["Dashboard", "Monthly Summary", "Tracking System"])
    st.sidebar.markdown("---")

    # ডাটা লোডিং (Dashboard এবং Tracking এর জন্য)
    if page == "Dashboard" or page == "Tracking System":
        df_raw = get_data()
        
        st.sidebar.markdown("## Global Filters")
        start_date = st.sidebar.date_input("Start Date", df_raw['date'].min())
        end_date = st.sidebar.date_input("End Date", df_raw['date'].max())
        
        team_list = ["All"] + sorted(df_raw['Team'].unique().tolist())
        team_selected = st.sidebar.selectbox("Team Name", team_list)
        shift_selected = st.sidebar.selectbox("Shift", ["All"] + sorted(df_raw['Shift'].unique().tolist()))
        emp_type_selected = st.sidebar.selectbox("Employee Type", ["All", "Artist", "QC"])
        product_selected_global = st.sidebar.selectbox("Product Filter", ["All", "Floorplan Queue", "Measurement Queue", "Autocad Queue", "Rework", "Urban Angles", "Van Bree Media"])

        # ফিল্টারিং লজিক
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

    # --- ৪. ড্যাশবোর্ড পেজ (আগের সব ফিচার সহ) ---
    if page == "Dashboard":
        st.markdown("<h2 style='text-align: center;'>Performance Analytics 2025</h2>", unsafe_allow_html=True)
        
        m1, m2, m3, m4, m5, m6, m7 = st.columns(7)
        with m1: st.markdown(f'<div class="metric-card rework-border">Rework AVG<br><h2>{calculate_man_day_avg(df, "Floorplan Queue", "Rework")}</h2></div>', unsafe_allow_html=True)
        with m2: st.markdown(f'<div class="metric-card fp-border">FP AVG<br><h2>{calculate_man_day_avg(df, "Floorplan Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m3: st.markdown(f'<div class="metric-card mrp-border">MRP AVG<br><h2>{calculate_man_day_avg(df, "Measurement Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m4: st.markdown(f'<div class="metric-card cad-border">CAD AVG<br><h2>{calculate_man_day_avg(df, "Autocad Queue", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m5: st.markdown(f'<div class="metric-card ua-border">UA AVG<br><h2>{calculate_man_day_avg(df, "Urban Angles", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m6: st.markdown(f'<div class="metric-card vanbree-border">Van Bree AVG<br><h2>{calculate_man_day_avg(df, "Van Bree Media", "Live Job")}</h2></div>', unsafe_allow_html=True)
        with m7: st.markdown(f'<div class="metric-card total-border">Total Order<br><h2>{len(df)}</h2></div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        tab1, tab2, tab3 = st.tabs(["📉 Overview", "👥 Team & Artist Summary", "🎨 Artist Analysis"])

        with tab1:
            c1, c2 = st.columns([2, 1])
            with c1:
                trend_df = df.groupby('date').size().reset_index(name='Orders')
                st.plotly_chart(px.line(trend_df, x='date', y='Orders', markers=True), use_container_width=True)
            with c2:
                st.subheader("🏆 Leaderboard")
                tops = df.groupby('Name').size().sort_values(ascending=False).head(5)
                for n, c in tops.items(): st.info(f"**{n}** - {c} Orders")

        with tab2:
            st.subheader("Detailed Team Performance")
            team_sum = df.groupby(['Team', 'Shift']).agg(Present=('Name', 'nunique'), Orders=('Ticket ID', 'count'), Time=('Time', 'sum'), Rework=('Job Type', lambda x: (x == 'Rework').sum()), FP=('Product', lambda x: (x == 'Floorplan Queue').sum()), MRP=('Product', lambda x: (x == 'Measurement Queue').sum()), CAD=('Product', lambda x: (x == 'Autocad Queue').sum()), UA=('Product', lambda x: (x == 'Urban Angles').sum()), VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()), SQM=('SQM', 'sum')).reset_index()
            st.dataframe(team_sum, use_container_width=True, hide_index=True)
            st.markdown("---")
            st.subheader("Performance Breakdown Section (Artist Summary)")
            artist_brk = df.groupby(['Name', 'Team', 'Shift']).agg(Order=('Ticket ID', 'count'), Time=('Time', 'sum'), Rework=('Job Type', lambda x: (x == 'Rework').sum()), FP=('Product', lambda x: (x == 'Floorplan Queue').sum()), MRP=('Product', lambda x: (x == 'Measurement Queue').sum()), UA=('Product', lambda x: (x == 'Urban Angles').sum()), CAD=('Product', lambda x: (x == 'Autocad Queue').sum()), VanBree=('Product', lambda x: (x == 'Van Bree Media').sum()), SQM=('SQM', 'sum'), days=('date', 'nunique')).reset_index()
            artist_brk['Idle'] = (artist_brk['days'] * 400) - artist_brk['Time']
            artist_brk['Idle'] = artist_brk['Idle'].apply(lambda x: max(0, x))
            st.dataframe(artist_brk.sort_values(by='Order', ascending=False), use_container_width=True, hide_index=True, height=750)

        with tab3:
            u_names = sorted(df['Name'].unique().tolist())
            a_sel = st.selectbox("Select Artist", u_names, key="dash_artist_tab3_v2")
            a_df = df[df['Name'] == a_sel]
            
            st.markdown(f"#### 🎨 Performance Insights: {a_sel}")
            
            # রঙিন মেট্রিক কার্ড রো
            i1, i2, i3, i4, i5, i6, i7 = st.columns(7)
            
            # ক্যালকুলেশন
            r_avg = calculate_man_day_avg(a_df, "Floorplan Queue", "Rework")
            f_avg = calculate_man_day_avg(a_df, "Floorplan Queue")
            m_avg = calculate_man_day_avg(a_df, "Measurement Queue")
            c_avg = calculate_man_day_avg(a_df, "Autocad Queue")
            u_avg = calculate_man_day_avg(a_df, "Urban Angles")
            v_avg = calculate_man_day_avg(a_df, "Van Bree Media")
            
            i1.markdown(f'<div class="metric-box cl-rework"><small>Rework Avg</small><br><b>{r_avg}</b></div>', unsafe_allow_html=True)
            i2.markdown(f'<div class="metric-box cl-fp"><small>FP Avg</small><br><b>{f_avg}</b></div>', unsafe_allow_html=True)
            i3.markdown(f'<div class="metric-box cl-mrp"><small>MRP Avg</small><br><b>{m_avg}</b></div>', unsafe_allow_html=True)
            i4.markdown(f'<div class="metric-box cl-cad"><small>CAD Avg</small><br><b>{c_avg}</b></div>', unsafe_allow_html=True)
            i5.markdown(f'<div class="metric-box cl-ua"><small>UA Avg</small><br><b>{u_avg}</b></div>', unsafe_allow_html=True)
            i6.markdown(f'<div class="metric-box cl-vb"><small>VB Avg</small><br><b>{v_avg}</b></div>', unsafe_allow_html=True)
            i7.markdown(f'<div class="metric-box cl-total"><small>Total Jobs</small><br><b>{len(a_df)}</b></div>', unsafe_allow_html=True)

            # অ্যাক্টিভিটি লগ চার্ট (পুরানো ডাটা ফেরত আনা হয়েছে)
            cll, crr = st.columns(2)
            with cll:
                p_data = a_df['Product'].value_counts().reset_index()
                p_data.columns = ['Product', 'Orders']
                st.plotly_chart(px.bar(p_data, x='Product', y='Orders', text='Orders', color='Product', height=350, title="Job Distribution"), use_container_width=True)
            with crr:
                st.plotly_chart(px.scatter(a_df, x="SQM", y="Time", size="Time", color="Product", height=350, title="SQM vs Time Efficiency"), use_container_width=True)
    # --- ৫. Monthly Summary (সম্পূর্ণ নতুন শিট থেকে) ---
    elif page == "Monthly Summary":
        df_summary = get_summary_data()
        # কলামের নামগুলো ক্লিন করা (যাতে শিটের সাথে হুবহু মেলে)
        df_summary.columns = [" ".join(c.split()).upper() for c in df_summary.columns]
        
        st.markdown("<h2 style='text-align: center; color: #1e293b; font-weight: 800;'>📊 Artist & QC Performance Intelligence</h2>", unsafe_allow_html=True)
        
        # ১. টপ সেকশন: লিডারবোর্ড (পয়েন্ট ১ অনুযায়ী ফিক্স করা হয়েছে)
        st.markdown("---")
        lb_col1, lb_col2 = st.columns([1.5, 1])
        
        with lb_col1:
            st.subheader("🏆 Leaderboard Analysis")
            l_type = st.radio("View Top 10 for:", ["ARTIST", "QC"], horizontal=True)
            
            # শিটের 'ARTIST/ QC' কলাম ব্যবহার করে ফিল্টার (পয়েন্ট ১ এর সমাধান)
            # স্ক্রিনশট অনুযায়ী কলাম বি এর নাম 'ARTIST/ QC'
            col_target = 'ARTIST/ QC' if 'ARTIST/ QC' in df_summary.columns else 'ARTIST/QC'
            
            top_filtered = df_summary[df_summary[col_target].str.strip().str.upper() == l_type.upper()]
            top_data = top_filtered.groupby('USER NAME ALL')['LIVE ORDER'].sum().sort_values(ascending=False).head(10).reset_index()
            
            if not top_data.empty:
                fig_top = px.bar(top_data, x='LIVE ORDER', y='USER NAME ALL', orientation='h', 
                                 text='LIVE ORDER', color='LIVE ORDER', color_continuous_scale='Blues')
                fig_top.update_layout(height=380, showlegend=False, yaxis={'categoryorder':'total ascending'})
                fig_top.update_traces(textposition='outside', cliponaxis=False)
                st.plotly_chart(fig_top, use_container_width=True)
            else:
                st.info(f"No data found for {l_type} in the '{col_target}' column.")
            
        with lb_col2:
            st.subheader("👥 Workload by Team")
            def identify_team(team_str):
                team_str = str(team_str).upper()
                if "RED" in team_str: return "Red Team"
                if "GREEN" in team_str: return "Green Team"
                if "BLUE" in team_str: return "Blue Team"
                if "FEMALE" in team_str: return "Female Team"
                return "Others"

            df_summary['TEAM_GROUP'] = df_summary['TEAM'].apply(identify_team)
            team_work = df_summary.groupby('TEAM_GROUP')['LIVE ORDER'].sum().reset_index()
            fig_team = px.bar(team_work, x='TEAM_GROUP', y='LIVE ORDER', text='LIVE ORDER', 
                              color='TEAM_GROUP', color_discrete_map={
                                  "Red Team": "#ef4444", "Green Team": "#10b981", 
                                  "Blue Team": "#3b82f6", "Female Team": "#ec4899", "Others": "#94a3b8"
                              })
            fig_team.update_layout(height=380, showlegend=False)
            st.plotly_chart(fig_team, use_container_width=True)

        # ২. আর্টিস্ট সিলেকশন
        st.markdown("---")
        f1, f2 = st.columns(2)
        with f1: a_sel = st.selectbox("👤 Select Artist/QC Name", sorted(df_summary['USER NAME ALL'].unique().tolist()), key="sum_a_v14")
        with f2: 
            m_list = sorted(df_summary['MONTH'].unique().tolist(), reverse=True)
            m_sel = st.multiselect("📅 Select Month (Pick 1 for Ranking)", m_list, key="sum_m_v14")
            
        s_df = df_summary[df_summary['USER NAME ALL'] == a_sel]
        if m_sel: s_df = s_df[s_df['MONTH'].isin(m_sel)]
        
        if not s_df.empty:
            # র‍্যাঙ্কিং ব্যাজ
            if len(m_sel) == 1:
                a_role = s_df[col_target].iloc[0]
                month_all = df_summary[(df_summary['MONTH'] == m_sel[0]) & (df_summary[col_target] == a_role)]
                rank_list = month_all.groupby('USER NAME ALL')['LIVE ORDER'].sum().sort_values(ascending=False)
                try:
                    artist_rank = rank_list.index.get_loc(a_sel) + 1
                    rank_badge = f"#{artist_rank} of {len(rank_list)}"
                except: rank_badge = "N/A"
            else: rank_badge = "Pick 1 Month"

            # ৩. KPI রঙিন কার্ডস (পয়েন্ট ৪)
            st.markdown("<br>", unsafe_allow_html=True)
            k_cols = st.columns(8)
            specs_data = [
                {"label": "Rank", "val": rank_badge, "cls": "cl-total"},
                {"label": "Live Orders", "val": int(s_df["LIVE ORDER"].sum()), "cls": "cl-total"},
                {"label": "Floorplan", "val": int(s_df["FLOORPLAN"].sum()), "cls": "cl-fp"},
                {"label": "Measurement", "val": int(s_df["MEASUREMENT"].sum()), "cls": "cl-mrp"},
                {"label": "AutoCAD", "val": int(s_df["AUTOCAD"].sum()), "cls": "cl-cad"},
                {"label": "UA", "val": int(s_df["URBAN ANGLES"].sum()), "cls": "cl-ua"},
                {"label": "VanBree", "val": int(s_df.get("VANBREEMEDIA", pd.Series([0])).sum()), "cls": "cl-vb"},
                {"label": "Rework", "val": int(s_df["RE_WORK"].sum()), "cls": "cl-rework"}
            ]
            for i, item in enumerate(specs_data):
                k_cols[i].markdown(f'<div class="metric-box {item["cls"]}"><small>{item["label"]}</small><br><b>{item["val"]}</b></div>', unsafe_allow_html=True)

            # ৪. এভারেজ চার্টস (পয়েন্ট ২: দশমিক ২ ঘর ও ভিজিবল ভ্যালু)
            st.markdown("<br>", unsafe_allow_html=True)
            c1, c2 = st.columns(2)
            with c1:
                st.subheader("📈 Average Orders Analysis")
                avg_ord_df = pd.DataFrame({
                    "Spec": ["FP", "MRP", "CAD", "UA", "VB", "RW"],
                    "Value": [
                        s_df['FP AVG'].mean(), s_df['MRP AVG'].mean(), s_df['CAD AVG'].mean(),
                        s_df['URBAN ANGLES'].sum()/20, s_df.get('VANBREEMEDIA', pd.Series([0])).sum()/20, s_df['RE_WORK'].sum()/20
                    ]
                })
                fig_avg_o = px.bar(avg_ord_df, x="Spec", y="Value", text="Value", color="Spec", height=380)
                fig_avg_o.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
                fig_avg_o.update_layout(yaxis_range=[0, avg_ord_df['Value'].max() * 1.4], showlegend=False)
                st.plotly_chart(fig_avg_o, use_container_width=True)

            with c2:
                st.subheader("⏱️ Average Time (Min)")
                def get_t_avg(t, o): return round(s_df[t].sum() / s_df[o].sum(), 2) if s_df[o].sum() > 0 else 0
                avg_t_map = {
                    "FP": get_t_avg('FP TIME', 'FLOORPLAN'), "MRP": get_t_avg('MRP TIME', 'MEASUREMENT'),
                    "CAD": get_t_avg('CAD TIME', 'AUTOCAD'), "UA": get_t_avg('URBAN ANGLES TIME', 'URBAN ANGLES'),
                    "RW": get_t_avg('RE_WORK TIME', 'RE_WORK')
                }
                fig_avg_t = px.bar(x=list(avg_t_map.keys()), y=list(avg_t_map.values()), text=list(avg_t_map.values()), color=list(avg_t_map.keys()), height=380)
                fig_avg_t.update_traces(texttemplate='%{text:.2f}', textposition='outside', cliponaxis=False)
                fig_avg_t.update_layout(yaxis_range=[0, max(avg_t_map.values()) * 1.4], showlegend=False)
                st.plotly_chart(fig_avg_t, use_container_width=True)

            # ৫. গেজ এবং রাডার
            st.markdown("---")
            rc1, rc2 = st.columns([1, 1])
            with rc1:
                st.subheader("🎯 Quality Status")
                re_rate = round((s_df['RE_WORK'].sum() / s_df['LIVE ORDER'].sum() * 100), 2) if s_df['LIVE ORDER'].sum() > 0 else 0
                import plotly.graph_objects as go
                fig_g = go.Figure(go.Indicator(mode="gauge+number", value=re_rate, gauge={'axis': {'range': [0, 10]}, 'bar': {'color': "#ef4444"}, 'steps': [{'range': [0, 2], 'color': "#dcfce7"}, {'range': [2, 5], 'color': "#fef9c3"}]}, title={'text': "Rework %"}))
                fig_g.update_layout(height=350)
                st.plotly_chart(fig_g, use_container_width=True)
            with rc2:
                st.subheader("🧬 Skill Balance")
                r_vals = [s_df['FLOORPLAN'].sum(), s_df['MEASUREMENT'].sum(), s_df['AUTOCAD'].sum(), s_df['URBAN ANGLES'].sum(), s_df.get('VANBREEMEDIA', pd.Series([0])).sum()]
                fig_r = go.Figure(data=go.Scatterpolar(r=r_vals, theta=['FP','MRP','CAD','UA','VB'], fill='toself'))
                fig_r.update_layout(height=350, polar=dict(radialaxis=dict(visible=False)))
                st.plotly_chart(fig_r, use_container_width=True)

            # ৬. নতুন সেকশন: ফুল ডাটা রেকর্ড লজ (আপনার চাহিদা অনুযায়ী)
            st.markdown("---")
            st.subheader(f"📋 Monthly Detailed Record: {a_sel}")
            cols_to_show = [
                'MONTH', 'DAY', 'LIVE ORDER', 'FLOORPLAN', 'MEASUREMENT', 'AUTOCAD', 'VANBREEMEDIA', 'RE_WORK',
                'FP TIME', 'MRP TIME', 'CAD TIME', 'URBAN ANGLES TIME', 'RE_WORK TIME', 'WORKING TIME',
                'TUESDAY TO FRIDAY AVG', 'SATURDAY TO MONDAY'
            ]
            # কলামগুলো শিটে আছে কি না তা নিশ্চিত করা
            existing_cols = [c for c in cols_to_show if c in s_df.columns]
            st.dataframe(s_df[existing_cols], use_container_width=True, hide_index=True)

        else:
            st.warning("No data found for the selected artist/month.")
    # --- ৬. ট্র্যাকিং সিস্টেম পেজ ---
    elif page == "Tracking System":
        st.title("Performance Tracking")
        criteria = st.selectbox("Criteria", ["All", "Short IP", "Spending More Time", "High Time vs SQM"])
        tdf = df.copy()
        tdf['RT Link'] = tdf['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
        
        s_mt = (((tdf['Employee Type'] == 'QC') & (tdf['Time'] > 20)) | ((tdf['Employee Type'] == 'Artist') & ((tdf['Time'] >= 150) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] > 40)))))
        if criteria == "Short IP": tdf = tdf[(((tdf['Employee Type'] == 'QC') & (tdf['Time'] < 2)) | ((tdf['Employee Type'] == 'Artist') & (((tdf['Product'] == 'Floorplan Queue') & (tdf['Time'] <= 15)) | ((tdf['Product'] == 'Measurement Queue') & (tdf['Time'] < 5)) | (~tdf['Product'].isin(['Floorplan Queue', 'Measurement Queue']) & (tdf['Time'] <= 10)))))]
        elif criteria == "Spending More Time": tdf = tdf[s_mt]
        elif criteria == "High Time vs SQM": tdf = tdf[(tdf['Time'] > (tdf['SQM'] + 15)) & ~s_mt]
        
        st.metric("Total Jobs Found", len(tdf))
        cols_to_show = ['Shift', 'Time', 'Ticket ID', 'RT Link', 'Name', 'date', 'Product', 'SQM', 'Floor', 'Labels', 'Job Type', 'Team']
        st.dataframe(tdf[cols_to_show], column_config={"RT Link": st.column_config.LinkColumn("RT", display_text="Open")}, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Error: {e}")
