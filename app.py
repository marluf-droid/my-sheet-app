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
    
    /* ১. মূল কার্ডের স্টাইল এবং অ্যানিমেশন সেট করা */
    .metric-card { 
        padding: 15px; 
        border-radius: 12px; 
        text-align: center; 
        color: #1e293b; 
        background: #ffffff; 
        border-top: 5px solid #e2e8f0;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease-in-out; /* এটি অ্যানিমেশনকে স্মুথ করবে */
        cursor: pointer;
    }

    /* ২. মাউস নিলে যে ইফেক্ট হবে (Highlight Effect) */
    .metric-card:hover {
        transform: translateY(-8px); /* কার্ডটি ৮ পিক্সেল ওপরে উঠে আসবে */
        box-shadow: 0 12px 20px rgba(0, 0, 0, 0.15); /* ছায়া আরও গভীর হবে */
        border-bottom: 2px solid rgba(0, 0, 0, 0.05); /* নিচে হালকা বর্ডার যোগ হবে */
    }
            /* ১. Performance Insights এবং Monthly Summary কার্ডের জন্য ট্রানজিশন সেট করা */
    .metric-box, .metric-card-box {
        transition: all 0.3s ease-in-out;
        cursor: pointer;
    }

    /* ২. মাউস নিলে এই কার্ডগুলোও ওপরের দিকে ভেসে উঠবে এবং শ্যাডো বাড়বে */
    .metric-box:hover, .metric-card-box:hover {
        transform: translateY(-5px); /* ৫ পিক্সেল ওপরে উঠবে */
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1); /* শ্যাডো বা ছায়া গভীর হবে */
        filter: brightness(1.03); /* সামান্য উজ্জ্বল হবে */
    }
            /* ১. পেজ লোড হওয়ার সময় নিচ থেকে উপরে ভেসে ওঠার অ্যানিমেশন তৈরি */
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(40px); /* ৪০ পিক্সেল নিচ থেকে শুরু হবে */
        }
        to {
            opacity: 1;
            transform: translateY(0); /* আগের জায়গায় ফিরে আসবে */
        }
    }

    /* ২. স্ট্রীমলিটের মেইন কন্টেন্ট ব্লককে টার্গেট করে অ্যানিমেশন অ্যাপ্লাই করা */
    .main .block-container {
        animation: fadeInUp 0.8s ease-out;
    }

    /* ৩. কার্ডগুলোর জন্য একটু দেরি করে অ্যানিমেশন হওয়া (Optional: পপ-আপ ইফেক্ট) */
    .metric-card, .metric-box, .metric-card-box {
        animation: fadeInUp 1s ease-out;
    }
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
            /* নতুন ড্যাশবোর্ড হেডার */
    .dashboard-header-modern {
        background: linear-gradient(90deg, #0f172a 0%, #1e293b 100%);
        color: white; padding: 25px; border-radius: 15px; 
        margin-bottom: 25px; text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.1);
    }
    /* উন্নত মেট্রিক কার্ড */
    .sleek-card-modern {
        background: white; padding: 18px; border-radius: 12px;
        text-align: center; border-top: 5px solid #ccc;
        box-shadow: 0 2px 10px rgba(0,0,0,0.05);
        transition: transform 0.3s ease;
    }
    .sleek-card-modern:hover { transform: translateY(-5px); }
    .sleek-card-modern h2 { margin: 8px 0 0 0; font-size: 26px; color: #1e293b; }
    .sleek-card-modern small { color: #64748b; font-weight: 700; text-transform: uppercase; font-size: 11px; }
            /* --- আধুনিক গ্লাস-বক্স ট্যাব ডিজাইন --- */
    /* ১. ট্যাব লিস্টের কন্টেইনার (Glass Background) */
    [data-baseweb="tab-list"] {
        background: rgba(241, 245, 249, 0.5) !important;
        backdrop-filter: blur(8px);
        border-radius: 12px !important;
        padding: 6px !important;
        gap: 10px !important;
        border: 1px solid rgba(226, 232, 240, 0.8);
        margin-bottom: 20px;
    }

    /* ২. প্রতিটি ট্যাব (Normal State) */
    .stTabs [data-baseweb="tab"] {
        background-color: transparent !important;
        border-radius: 10px !important;
        padding: 8px 20px !important;
        font-weight: 600 !important;
        color: #64748b !important;
        transition: all 0.3s ease !important;
        border: none !important;
    }

    /* ৩. একটিভ ট্যাব হাইলাইট (Glass Box Curve Effect) */
    .stTabs [aria-selected="true"] {
        background-color: white !important;
        color: #3b82f6 !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08) !important;
        transform: scale(1.02);
    }

    /* ৪. মাউস নিলে হালকা গ্লো হবে */
    .stTabs [data-baseweb="tab"]:hover {
        color: #3b82f6 !important;
        background: rgba(255, 255, 255, 0.5) !important;
    }

    /* ৫. ডিফল্ট নিচের লাল লাইনটি বন্ধ করা */
    .stTabs [data-baseweb="tab-highlight"] {
        background-color: transparent !important;
    }
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
def get_data(sheet_id):
    client = get_gspread_client()
    spreadsheet = client.open_by_key(sheet_id)
    df = pd.DataFrame(spreadsheet.worksheet("DATA").get_all_records())
    
    # ১. কলামের নামগুলো থেকে অতিরিক্ত স্পেস মুছে ফেলা
    df.columns = [c.strip() for c in df.columns]
    
    # ২. জানুয়ারী শিটে "Team name" বা অন্য কোনো ভার্সন থাকলে সেটাকে "Team" এ রূপান্তর করা
    # এটি খুবই জরুরি কারণ আপনার কোড সব জায়গায় 'Team' খুঁজছে
    rename_dict = {
        'Team name': 'Team',
        'Team Name': 'Team',
        'TEAM NAME': 'Team',
        'TEAM': 'Team'
    }
    df = df.rename(columns=rename_dict)

    # যদি কোনো কারণে 'Team' কলাম না পাওয়া যায়, তবে একটি খালি কলাম তৈরি করবে যাতে এরর না আসে
    if 'Team' not in df.columns:
        df['Team'] = 'Unknown'

    # ৩. তারিখ কনভার্ট করা এবং খালি রো মুছে ফেলা (আগের এররটির সমাধান)
    df['date'] = pd.to_datetime(df['date'], errors='coerce')
    df = df.dropna(subset=['date']) 
    df['date'] = df['date'].dt.date
    
    # ৪. কলাম ভ্যালু নিউমেরিক করা
    df['Time'] = pd.to_numeric(df['Time'], errors='coerce').fillna(0)
    df['SQM'] = pd.to_numeric(df['SQM'], errors='coerce').fillna(0)
    
    # ৫. ডাটা ক্লিন করা
    text_cols = ['Product', 'Job Type', 'Employee Type', 'Team', 'Name', 'Shift']
    for col in text_cols:
        if col in df.columns: 
            df[col] = df[col].astype(str).str.strip()
            
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
        # ১. ডাটা সোর্স অপশন
        st.sidebar.markdown("##  Data Selection")
        
        # ড্রপডাউনে একটি 'Manual Input' অপশন যোগ করা হয়েছে
        options = ["January 2026", "December 2025", "Connect New Sheet (Manual)"]
        selected_option = st.sidebar.selectbox("Select Data Month", options)

        # ২. লজিক: যদি ম্যানুয়াল সিলেক্ট করা হয় তবে ইনপুট বক্স দেখাবে
        if selected_option == "Connect New Sheet (Manual)":
            active_sheet_id = st.sidebar.text_input("Paste Sheet ID here", placeholder="e.g. 1lQJQkXNvsdnN8pwsI4...")
            selected_month = "Custom Data" # হেডারের জন্য নাম
            
            if not active_sheet_id:
                st.sidebar.info(" Please paste the Google Sheet ID above.")
                st.stop() # আইডি না দেওয়া পর্যন্ত নিচের কোড চলবে না
        else:
            # আগের সেভ করা আইডিগুলো
            data_sources = {
                "January 2026": "1lQJQkXNvsdnN8pwsI4QhctS7Pk0M0D6FVklLvYKPNmc",
                "December 2025": "1e-3jYxjPkXuxkAuSJaIJ6jXU0RT1LemY6bBQbCTX_6Y"
            }
            active_sheet_id = data_sources[selected_option]
            selected_month = selected_option

        # ডাটা লোড করা
        df_raw = get_data(active_sheet_id)
        
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
        tab1, tab2, tab3 = st.tabs(["📉 Overview", " Team & Artist Summary", " Artist Analysis"])

        with tab1:
            c1, c2 = st.columns([2, 1])
            with c1:
                trend_df = df.groupby('date').size().reset_index(name='Orders')
                st.plotly_chart(px.line(trend_df, x='date', y='Orders', markers=True), use_container_width=True)
            with c2:
                st.subheader(" Leaderboard")
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
            
            st.markdown(f"####  Performance Insights: {a_sel}")
            
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
                st.subheader("Job Distribution (All Specs)")
                
                # ১. প্রতিটি সেকশনের জন্য আলাদাভাবে কাউন্ট ক্যালকুলেট করা (মেট্রিক কার্ডের সাথে মিল রেখে)
                dist_data = {
                    "Category": ["Rework", "FP", "MRP", "CAD", "UA", "VB"],
                    "Count": [
                        len(a_df[a_df['Job Type'] == 'Rework']),
                        len(a_df[(a_df['Product'] == 'Floorplan Queue') & (a_df['Job Type'] == 'Live Job')]),
                        len(a_df[(a_df['Product'] == 'Measurement Queue') & (a_df['Job Type'] == 'Live Job')]),
                        len(a_df[(a_df['Product'] == 'Autocad Queue') & (a_df['Job Type'] == 'Live Job')]),
                        len(a_df[(a_df['Product'] == 'Urban Angles') & (a_df['Job Type'] == 'Live Job')]),
                        len(a_df[(a_df['Product'] == 'Van Bree Media') & (a_df['Job Type'] == 'Live Job')])
                    ]
                }
                
                # ২. ডাটাফ্রেম তৈরি করা
                chart_df = pd.DataFrame(dist_data)
                
                # ৩. বার চার্ট তৈরি করা (স্মুথ কালার প্যালেট সহ)
                fig_dist = px.bar(
                    chart_df, 
                    x='Category', 
                    y='Count', 
                    text='Count', 
                    color='Category',
                    color_discrete_sequence=px.colors.qualitative.Pastel, # সুন্দর স্মুথ কালার
                    height=400
                )
                
                # ৪. চার্টের লেআউট এবং ভ্যালু ভিজিবিলিটি ঠিক করা
                fig_dist.update_traces(textposition='outside', cliponaxis=False)
                fig_dist.update_layout(
                    showlegend=False, 
                    xaxis_title=None, 
                    yaxis_title="Total Orders",
                    yaxis_range=[0, chart_df['Count'].max() * 1.2], # ওপরের ভ্যালু যাতে কেটে না যায়
                    margin=dict(t=20, b=20, l=10, r=10)
                )
                
                st.plotly_chart(fig_dist, use_container_width=True)
            with crr:
                st.subheader("SQM vs Time Efficiency")
                
                # ১. ডাটা প্রিপারেশন এবং লিঙ্ক তৈরি
                a_plot_df = a_df.copy()
                a_plot_df['RT_Link'] = a_plot_df['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")

                # ২. স্কেটার প্লট তৈরি
                fig_s = px.scatter(
                    a_plot_df, 
                    x="SQM", 
                    y="Time", 
                    size="Time", 
                    color="Product", 
                    hover_data={'Ticket ID': True, 'SQM': True, 'Time': True},
                    custom_data=['Ticket ID', 'RT_Link'], # এখানে ডাটা ইনজেক্ট করা হয়েছে
                    height=400
                )
                
                # ডট সিলেক্ট করলে সেটি লাল দেখাবে যাতে বোঝা যায় কোনটি ক্লিক হয়েছে
                fig_s.update_traces(selected=dict(marker=dict(color='red', size=15)))

                # ৩. চার্ট ডিসপ্লে (on_select="rerun" ব্যবহার করে)
                selection = st.plotly_chart(fig_s, use_container_width=True, on_select="rerun", key="sqm_efficiency_chart")

                # ৪. বাটন দেখানোর নিরাপদ লজিক (Error handling সহ)
                if selection and "selection" in selection:
                    points = selection["selection"].get("points", [])
                    if points:
                        try:
                            # প্রথম পয়েন্টটি নেওয়া
                            target_point = points[0]
                            
                            # 'custom_data' বা 'customdata' যেকোনো একটির জন্য চেক করা (এটিই এরর ফিক্স করবে)
                            c_data = target_point.get("custom_data") or target_point.get("customdata")
                            
                            if c_data:
                                t_id = c_data[0]
                                t_url = c_data[1]
                                
                                # চার্টের ঠিক নিচে সুন্দর করে বাটন দেখানো
                                st.success(f"Selected Ticket: #{t_id}")
                                st.link_button(f" Open Ticket #{t_id} in RT", t_url, use_container_width=True, type="primary")
                            else:
                                st.error("Link data missing in the selected point.")
                        except Exception as e:
                            st.error(f"Selection processing error: {e}")
                    else:
                        # কিছুই সিলেক্ট না থাকলে এই গাইডটি দেখাবে
                        st.info("**Instruction:** Click exactly on a dot in the chart above to see the RT Link button here.")
            st.markdown("---")
            st.subheader(f"📋 Artist Performance Detail ")
            
            # আর্টিস্টের ডাটা কপি করা
            log_df = a_df.copy()

            # শিটে কলামগুলো সাধারণত যে ক্রমে থাকে (আপনার DATA ট্যাবের ক্রম অনুযায়ী)
            # আপনি চাইলে এখানে আপনার শিটের কলামের ক্রম অনুযায়ী নামগুলো আগে-পিছে করতে পারেন
            sheet_cols = ['date', 'Ticket ID', 'Product', 'SQM', 'Floor', 'Labels', 'Time', 'Job Type', 'Shift']
            
            # শিটে থাকা শুধুমাত্র বিদ্যমান কলামগুলো ফিল্টার করা
            display_cols = [c for c in sheet_cols if c in log_df.columns]

            # আরটি লিঙ্ক (RT Link) টি যোগ রাখা হলো কারণ এটি কাজের সুবিধার জন্য প্রয়োজন
            if 'Ticket ID' in log_df.columns:
                log_df['RT Link'] = log_df['Ticket ID'].apply(lambda x: f"https://tickets.bright-river.cc/Ticket/Display.html?id={x}")
                if 'Ticket ID' in display_cols:
                    idx = display_cols.index('Ticket ID') + 1
                    display_cols.insert(idx, 'RT Link')

            # ডাটাফ্রেমটি ডিসপ্লে করা
            st.dataframe(
                log_df[display_cols].sort_values('date', ascending=False),
                column_config={"RT Link": st.column_config.LinkColumn("RT", display_text="Open")},
                use_container_width=True, 
                hide_index=True
            )
    # --- ৫. Monthly Summary (সম্পূর্ণ নতুন শিট থেকে) ---
    elif page == "Monthly Summary":
        df_summary = get_summary_data()
        df_summary.columns = [" ".join(c.split()).upper() for c in df_summary.columns]
        col_role = 'ARTIST/ QC' if 'ARTIST/ QC' in df_summary.columns else 'ARTIST/QC'

        # --- আধুনিক স্লিক CSS ---
        st.markdown("""
            <style>
            .compact-header {
                background: linear-gradient(90deg, #1e293b 0%, #334155 100%);
                color: white; padding: 12px 25px; border-radius: 15px; margin-bottom: 20px;
                display: flex; justify-content: space-between; align-items: center;
            }
            /* মেইন ৪টি কার্ডের জন্য স্পেশাল ডিজাইন */
            .main-metric-card {
                background: #ffffff; border-radius: 15px; padding: 20px;
                border: 1px solid #e2e8f0; box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05);
                text-align: center; height: 170px; display: flex; flex-direction: column;
                justify-content: center; align-items: center; transition: 0.3s;
            }
            .main-metric-card:hover { transform: translateY(-5px); box-shadow: 0 10px 15px rgba(0,0,0,0.05); }
            
            .score-circle-v2 {
                background: #f8fafc; border-radius: 50%; width: 75px; height: 75px;
                display: flex; align-items: center; justify-content: center;
                border: 4px solid #3b82f6; margin-bottom: 5px; color: #1e293b;
            }
            .info-card-sleek {
                padding: 10px; border-radius: 12px; text-align: center;
                border: 1px solid rgba(0,0,0,0.05);
            }
            </style>
        """, unsafe_allow_html=True)

        # ১. হেডার
        st.markdown('<div class="compact-header"><h2 style="margin:0;"> Intelligence Hub</h2><p style="margin:0; opacity:0.8;">Performance Dashboard</p></div>', unsafe_allow_html=True)

        # ২. লিডারবোর্ড এবং ফিল্টার
        top_col1, top_col2 = st.columns([1.5, 1])
        with top_col1:
            st.markdown("#####  Leaderboard Analysis")
            l_type_sum = st.radio("Show Top 10 for:", ["ARTIST", "QC"], horizontal=True, key="role_top_v24")
            top_filt = df_summary[df_summary[col_role].str.strip().str.upper() == l_type_sum]
            top_10_df = top_filt.groupby('USER NAME ALL')['LIVE ORDER'].sum().sort_values(ascending=False).head(10).reset_index()
            fig_top_bar = px.bar(top_10_df, x='LIVE ORDER', y='USER NAME ALL', orientation='h', text='LIVE ORDER', height=300, color='LIVE ORDER', color_continuous_scale='Blues')
            fig_top_bar.update_layout(showlegend=False, margin=dict(t=10, b=10), yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig_top_bar, use_container_width=True)

        with top_col2:
            st.markdown("##### ⚙️ Selection & Controls")
            l_role = st.selectbox("Identify Role", ["ARTIST", "QC"], index=0 if l_type_sum=="ARTIST" else 1)
            names_list = sorted(df_summary[df_summary[col_role].str.strip().str.upper() == l_role]['USER NAME ALL'].unique().tolist())
            a_sel = st.selectbox(f"Choose {l_role}", names_list, key="sum_a_v24")
            m_list_all = sorted(df_summary['MONTH'].unique().tolist(), reverse=True)
            m_sel = st.multiselect("Filter Months", m_list_all, key="sum_m_v24")

        # ডাটা ফিল্টারিং
        s_df = df_summary[df_summary['USER NAME ALL'] == a_sel]
        if m_sel: s_df = s_df[s_df['MONTH'].isin(m_sel)]
        
        if not s_df.empty:
            # ক্যালকুলেশনস
            total_days = s_df['DAY'].sum() if s_df['DAY'].sum() > 0 else 1
            fp_mrp_avg = (s_df['FLOORPLAN'].sum() + s_df['MEASUREMENT'].sum()) / total_days
            daily_time_avg = s_df['WORKING TIME'].sum() / total_days
            perf_score = min(100, int((fp_mrp_avg / 5 * 50) + (daily_time_avg / 390 * 50)))
            
            # ৩. মেইন স্কোর কার্ডস (আপনার চাহিদা অনুযায়ী আগের সেই সুন্দর স্টাইল)
            st.markdown("<br>", unsafe_allow_html=True)
            sc1, sc2, sc3, sc4 = st.columns(4)
            
            with sc1:
                st.markdown(f'''<div class="main-metric-card">
                    <small style="color:#64748b; font-weight:bold;">PERFORMANCE SCORE</small>
                    <div class="score-circle-v2"><h3>{perf_score}</h3></div>
                    <small style="color:#3b82f6;">Efficiency Rating</small>
                </div>''', unsafe_allow_html=True)
            
            with sc2:
                st.markdown(f'''<div class="main-metric-card">
                    <small style="color:#64748b; font-weight:bold;">MONTHLY VOLUME</small>
                    <h1 style="margin:5px 0; color:#1e293b;">{int(s_df["LIVE ORDER"].sum())}</h1>
                    <small style="color:#64748b;">Total Orders Completed</small>
                </div>''', unsafe_allow_html=True)

            with sc3:
                st.markdown(f'''<div class="main-metric-card">
                    <small style="color:#64748b; font-weight:bold;">EFFICIENCY (ORD/DAY)</small>
                    <h1 style="margin:5px 0; color:#10b981;">{round(fp_mrp_avg, 2)}</h1>
                    <small style="color:#64748b;">Target: 5.0</small>
                </div>''', unsafe_allow_html=True)

            with sc4:
                st.markdown(f'''<div class="main-metric-card">
                    <small style="color:#64748b; font-weight:bold;">DAILY TIME AVG</small>
                    <h1 style="margin:5px 0; color:#f59e0b;">{int(daily_time_avg)}m</h1>
                    <small style="color:#64748b;">Target: 390m</small>
                </div>''', unsafe_allow_html=True)

            # ৪. রঙিন ৮টি KPI কার্ড
            st.markdown("<br>", unsafe_allow_html=True)
            k_cols = st.columns(7)
            
            # র‍্যাঙ্কিং লজিক
            a_type = s_df[col_role].iloc[0]
            r_base = df_summary[(df_summary['MONTH'] == m_sel[0]) & (df_summary[col_role] == a_type)] if len(m_sel) == 1 else df_summary[df_summary[col_role] == a_type]
            r_list = r_base.groupby('USER NAME ALL')['LIVE ORDER'].sum().sort_values(ascending=False)
            try: r_idx = r_list.index.get_loc(a_sel) + 1; r_badge = f"#{r_idx}"
            except: r_badge = "N/A"

            kpi_data = [
                {"label": "Rank", "val": r_badge, "cls": "cl-total"},
                {"label": "Floorplan", "val": int(s_df["FLOORPLAN"].sum()), "cls": "cl-fp"},
                {"label": "Measurement", "val": int(s_df["MEASUREMENT"].sum()), "cls": "cl-mrp"},
                {"label": "AutoCAD", "val": int(s_df["AUTOCAD"].sum()), "cls": "cl-cad"},
                {"label": "UA", "val": int(s_df["URBAN ANGLES"].sum()), "cls": "cl-ua"},
                {"label": "VanBree", "val": int(s_df.get("VANBREEMEDIA", pd.Series([0])).sum()), "cls": "cl-vb"},
                {"label": "Rework", "val": int(s_df["RE_WORK"].sum()), "cls": "cl-rework"}
            ]
            for i, item in enumerate(kpi_data):
                k_cols[i].markdown(f'<div class="info-card-sleek {item["cls"]}"><small>{item["label"]}</small><br><b>{item["val"]}</b></div>', unsafe_allow_html=True)

            # ৫. চার্ট সেকশন
            st.markdown("---")
            c_a, c_b = st.columns(2)
            spec_colors = {"FP": "#3b82f6", "MRP": "#10b981", "CAD": "#f59e0b", "UA": "#8b5cf6", "VB": "#06b6d4", "RW": "#f43f5e"}
            with c_a:
                v_df = pd.DataFrame({"Spec": ["FP", "MRP", "CAD", "UA", "VB", "RW"], "Val": [s_df['FLOORPLAN'].sum()/total_days, s_df['MEASUREMENT'].sum()/total_days, s_df['AUTOCAD'].sum()/total_days, s_df['URBAN ANGLES'].sum()/total_days, s_df.get('VANBREEMEDIA', pd.Series([0])).sum()/total_days, s_df['RE_WORK'].sum()/total_days]})
                st.plotly_chart(px.bar(v_df, x="Spec", y="Val", color="Spec", color_discrete_map=spec_colors, text_auto='.2f', height=350, title="Order Avg Distribution"), use_container_width=True)
            with c_b:
                def get_t(t, o): return round(s_df[t].sum() / s_df[o].sum(), 2) if s_df[o].sum() > 0 else 0
                t_df = pd.DataFrame({"Spec": ["FP", "MRP", "CAD", "UA", "RW"], "Time": [get_t('FP TIME','FLOORPLAN'), get_t('MRP TIME','MEASUREMENT'), get_t('CAD TIME','AUTOCAD'), get_t('URBAN ANGLES TIME','URBAN ANGLES'), get_t('RE_WORK TIME','RE_WORK')]})
                st.plotly_chart(px.bar(t_df, x="Spec", y="Time", color="Spec", color_discrete_map=spec_colors, text_auto='.1f', height=350, title="Avg Processing Time (Min)"), use_container_width=True)

            # ৬. Detailed Record Table (পয়েন্ট ৪ এর সমাধান)
            st.markdown("---")
            st.markdown("#####  Detailed Monthly Records")
            target_cols = [
                'MONTH', 'DAY', 'LIVE ORDER', 'FP TIME', 'MRP TIME', 'CAD TIME', 
                'URBAN ANGLES TIME', 'RE_WORK TIME', 'WORKING TIME', 
                'TUESDAY TO FRIDAY AVG', 'SATURDAY TO MONDAY', 'FP/MRP AVG'
            ]
            available_cols = [c for c in target_cols if c in s_df.columns]
            st.dataframe(s_df[available_cols], use_container_width=True, hide_index=True)

        else:
            st.warning("No data found for the current selection.")
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
