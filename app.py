import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="Port Lookahead Dashboard", layout="wide")

# Header with professional styling
st.title(" Port Lookahead Dashboard")
st.markdown("Upload your Excel file with vessel schedule (ETA / ETD) and analyze arrivals, occupancy and departures.")

# Footer with developer credit (discreet)
st.markdown("""
<style>
.footer {
    position: fixed;
    bottom: 0;
    right: 10px;
    font-size: 10px;
    color: #888;
    padding: 5px;
    z-index: 999;
}
</style>
<div class="footer">Developed by Josue Antonio Diaz Gomez | Assistant Engineer</div>
""", unsafe_allow_html=True)

# ---------- Helper: parse date/time ----------
def try_get_col(df, candidates):
    for c in candidates:
        if c in df.columns:
            return c
    return None

def parse_datetime_from_row(df, date_col, time_col, row_index):
    """Parse datetime handling Excel formats properly"""
    date_val = df.loc[row_index, date_col]
    time_val = df.loc[row_index, time_col]
    
    if pd.isna(date_val) or pd.isna(time_val):
        return None
    
    try:
        if isinstance(date_val, (pd.Timestamp, datetime)):
            date_part = pd.to_datetime(date_val).date()
        else:
            date_str = str(date_val).strip()
            date_part = pd.to_datetime(date_str, dayfirst=True).date()
        
        if isinstance(time_val, (pd.Timestamp, datetime)):
            time_part = pd.to_datetime(time_val).time()
        else:
            time_str = str(time_val).strip()
            if '.' in time_str:
                time_str = time_str.split('.')[0]
            time_part = pd.to_datetime(time_str, format='%H:%M:%S').time()
        
        return datetime.combine(date_part, time_part)
    
    except Exception as e:
        return None

# ---------- Upload file ----------
uploaded = st.file_uploader("Upload your Excel file (.xlsx)", type=["xlsx"])

if uploaded is None:
    st.info("⬆️ Please upload an Excel file to start the analysis.")
    st.stop()

try:
    df = pd.read_excel(uploaded)
    st.success(f"✅ File loaded: {len(df)} records found")
except Exception as e:
    st.error(f"❌ Error reading Excel: {e}")
    st.stop()

# ---------- Configuration - Date Range Only ----------
st.sidebar.header("⚙️ Configuration")

col_date1, col_date2 = st.sidebar.columns(2)
with col_date1:
    start_date = st.date_input("📅 Start date", value=datetime(2025,10,13).date())
with col_date2:
    end_date = st.date_input("📅 End date", value=(datetime(2025,10,13) + timedelta(days=7)).date())

# Convert to datetime (start of day for start_date, end of day for end_date)
current_dt = datetime.combine(start_date, datetime.min.time())
end_dt = datetime.combine(end_date, datetime.max.time())

# Validate that end_date is greater than start_date
if end_dt <= current_dt:
    st.sidebar.error("❌ End date must be after start date")
    st.stop()

analysis_days = (end_dt - current_dt).days
st.sidebar.markdown(f"**📊 Analysis Period:**")
st.sidebar.markdown(f"From: `{current_dt.strftime('%m/%d/%Y')}`")
st.sidebar.markdown(f"To: `{end_dt.strftime('%m/%d/%Y')}`")
st.sidebar.markdown(f"**Duration:** {analysis_days} days")

# ---------- Detect columns ----------
col_ship = try_get_col(df, ["SHIP","Ship","ship","Buque","BUQUE","NOMBRE","Vessel"])
col_arr_day = try_get_col(df, ["Arrival day","ArrivalDay","arrivalDay","Arrival_day","ETA date","Arrival date"])
col_arr_time = try_get_col(df, ["Arrival time","arrivalTime","ArrivalTime","ETA time","ETA"])
col_dep_day = try_get_col(df, ["Departure day","DepartureDay","depDay","Departure_day","ETD date","Departure date"])
col_dep_time = try_get_col(df, ["Departure time","departureTime","ETD time","ETD","Departure_time"])
col_berth = try_get_col(df, ["Arrival","Berth","Pier","Muelle","muelle","BERTH","Terminal"])
col_docking = try_get_col(df, ["Docking time (h)","DockingTime","dockingTime","Docking Time","Docking"])
col_est_docking = try_get_col(df, ["Estimated Docking Time (h)","EstDockingTime","estDockingTime","Est Docking Time","EstDocking"])
col_dwt = try_get_col(df, ["DWT","dwt","Deadweight","DeadWeight"])

# Validate critical columns
missing = []
if col_ship is None: missing.append("SHIP/Vessel")
if col_arr_day is None: missing.append("Arrival day")
if col_arr_time is None: missing.append("Arrival time")
if col_dep_day is None: missing.append("Departure day")
if col_dep_time is None: missing.append("Departure time")

if missing:
    st.error(f"❌ Missing critical columns: {', '.join(missing)}")
    st.write("**Columns detected in your file:**", list(df.columns))
    st.stop()

# ---------- Process data ----------
with st.spinner("Processing data..."):
    arrivals = []
    departures = []
    berths = []
    docking_times = []
    est_docking_times = []
    dwts = []
    ships = []

    for i in df.index:
        try:
            arr_dt = parse_datetime_from_row(df, col_arr_day, col_arr_time, i)
            dep_dt = parse_datetime_from_row(df, col_dep_day, col_dep_time, i)
            
            ship_val = df.loc[i, col_ship] if col_ship else f"Vessel_{i}"
            berth_val = df.loc[i, col_berth] if col_berth else None
            dock_val = df.loc[i, col_docking] if col_docking else None
            est_dock_val = df.loc[i, col_est_docking] if col_est_docking else None
            dwt_val = df.loc[i, col_dwt] if col_dwt else None
            
            ships.append(ship_val)
            arrivals.append(arr_dt)
            departures.append(dep_dt)
            berths.append(berth_val)
            docking_times.append(dock_val)
            est_docking_times.append(est_dock_val)
            dwts.append(dwt_val)
        except Exception as e:
            continue

    proc = pd.DataFrame({
        "SHIP": ships,
        "arrival_dt": arrivals,
        "departure_dt": departures,
        "Berth": berths,
        "DockingTime": docking_times,
        "EstDockingTime": est_docking_times,
        "DWT": dwts
    })

    proc_valid = proc.dropna(subset=["arrival_dt","departure_dt"]).copy()
    
    if proc_valid.empty:
        st.error("❌ Could not process valid data. Please check your file format.")
        st.stop()

# ---------- Classifications ----------
arriving = proc_valid[(proc_valid["arrival_dt"] >= current_dt) & (proc_valid["arrival_dt"] <= end_dt)].copy()
departing = proc_valid[(proc_valid["departure_dt"] >= current_dt) & (proc_valid["departure_dt"] <= end_dt)].copy()
in_port = proc_valid[(proc_valid["arrival_dt"] < end_dt) & (proc_valid["departure_dt"] > current_dt)].copy()

# ---------- KPIs ----------
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("🚢 Arrivals", len(arriving))
    dwt_arr = int(arriving['DWT'].sum()) if not arriving['DWT'].isna().all() and len(arriving) > 0 else 0
    st.caption(f"DWT: {dwt_arr:,}")

with col2:
    st.metric("⚓ In Port", len(in_port))
    dwt_port = int(in_port['DWT'].sum()) if not in_port['DWT'].isna().all() and len(in_port) > 0 else 0
    st.caption(f"DWT: {dwt_port:,}")

with col3:
    st.metric("🔄 Departures", len(departing))
    dwt_dep = int(departing['DWT'].sum()) if not departing['DWT'].isna().all() and len(departing) > 0 else 0
    st.caption(f"DWT: {dwt_dep:,}")

with col4:
    total_operations = len(arriving) + len(departing)
    st.metric("📋 Total Operations", total_operations)
    st.caption(f"In period")

# ---------- CHARTS ----------
st.markdown("---")
st.header("📊 Visualizations")

# Tabs for different charts
tab_gantt, tab_timeline, tab_berth, tab_dwt = st.tabs([
    "📅 Gantt Chart",
    "📈 Operations Timeline", 
    "🏗️ Berth Occupancy",
    "⚖️ DWT by Period"
])

with tab_gantt:
    st.subheader("Gantt Chart - Berth Occupancy")
    
    if in_port.empty:
        st.info("No vessels in port for the selected period.")
    else:
        # Prepare data for Gantt
        gantt_data = in_port.copy()
        gantt_data = gantt_data.sort_values(['Berth', 'arrival_dt'])
        
        # Create Gantt figure
        fig_gantt = px.timeline(
            gantt_data,
            x_start="arrival_dt",
            x_end="departure_dt",
            y="Berth",
            color="Berth",
            hover_data=["SHIP", "DWT", "DockingTime"],
            title="Berth Occupancy Over Time",
            labels={"arrival_dt": "Arrival", "departure_dt": "Departure"}
        )
        
        # Customize
        fig_gantt.update_yaxes(categoryorder="total ascending")
        fig_gantt.update_layout(
            height=max(400, len(gantt_data['Berth'].unique()) * 60),
            xaxis_title="Date and Time",
            yaxis_title="Berth",
            showlegend=True,
            hovermode='closest'
        )
        
        # Add vertical line for current date if in range
        now = datetime.now()
        if current_dt <= now <= end_dt:
            fig_gantt.add_vline(
                x=now.timestamp() * 1000,
                line_dash="dash",
                line_color="red",
                annotation_text="Now",
                annotation_position="top"
            )
        
        st.plotly_chart(fig_gantt, use_container_width=True)
        
        # Details table
        with st.expander("📋 View vessel details in port"):
            gantt_display = gantt_data[["SHIP", "Berth", "arrival_dt", "departure_dt", "DWT", "DockingTime"]].copy()
            gantt_display["arrival_dt"] = gantt_display["arrival_dt"].dt.strftime('%m/%d/%Y %H:%M')
            gantt_display["departure_dt"] = gantt_display["departure_dt"].dt.strftime('%m/%d/%Y %H:%M')
            gantt_display = gantt_display.rename(columns={
                "arrival_dt": "Arrival",
                "departure_dt": "Departure",
                "DockingTime": "Docking (h)"
            })
            st.dataframe(gantt_display, use_container_width=True)

with tab_timeline:
    st.subheader("Arrivals and Departures Timeline")
    
    # Create dataframe for timeline
    timeline_arrivals = arriving[["SHIP", "arrival_dt", "Berth"]].copy()
    timeline_arrivals["Type"] = "Arrival"
    timeline_arrivals = timeline_arrivals.rename(columns={"arrival_dt": "Date"})
    
    timeline_departures = departing[["SHIP", "departure_dt", "Berth"]].copy()
    timeline_departures["Type"] = "Departure"
    timeline_departures = timeline_departures.rename(columns={"departure_dt": "Date"})
    
    timeline_data = pd.concat([timeline_arrivals, timeline_departures]).sort_values("Date")
    
    if timeline_data.empty:
        st.info("No operations in the selected period.")
    else:
        # Temporal scatter plot
        fig_timeline = px.scatter(
            timeline_data,
            x="Date",
            y="Berth",
            color="Type",
            hover_data=["SHIP"],
            title="Operations Over Time",
            color_discrete_map={"Arrival": "#2E86AB", "Departure": "#A23B72"}
        )
        
        fig_timeline.update_traces(marker=dict(size=12, line=dict(width=1, color='white')))
        fig_timeline.update_layout(height=500, hovermode='closest')
        
        st.plotly_chart(fig_timeline, use_container_width=True)
        
        # Daily summary
        timeline_data["Day"] = timeline_data["Date"].dt.date
        daily_summary = timeline_data.groupby(["Day", "Type"]).size().reset_index(name="Count")
        
        fig_day = px.bar(
            daily_summary,
            x="Day",
            y="Count",
            color="Type",
            title="Operations per Day",
            barmode="group",
            color_discrete_map={"Arrival": "#2E86AB", "Departure": "#A23B72"}
        )
        fig_day.update_layout(height=400)
        st.plotly_chart(fig_day, use_container_width=True)

with tab_berth:
    st.subheader("Occupancy by Berth")
    
    if in_port.empty:
        st.info("No data to chart occupancy.")
    else:
        occ = in_port.groupby("Berth").agg({
            "SHIP": "count",
            "DWT": "sum",
            "DockingTime": "mean"
        }).reset_index()
        
        occ = occ.rename(columns={
            "SHIP": "Vessels",
            "DWT": "Total DWT",
            "DockingTime": "Avg Docking (h)"
        })
        
        col_g1, col_g2 = st.columns(2)
        
        with col_g1:
            fig_vessels = px.bar(
                occ,
                x="Berth",
                y="Vessels",
                title="Number of Vessels by Berth",
                color="Vessels",
                color_continuous_scale="Blues",
                text="Vessels"
            )
            fig_vessels.update_traces(textposition='outside')
            fig_vessels.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_vessels, use_container_width=True)
        
        with col_g2:
            fig_dwt = px.bar(
                occ,
                x="Berth",
                y="Total DWT",
                title="Total DWT by Berth",
                color="Total DWT",
                color_continuous_scale="Oranges"
            )
            fig_dwt.update_layout(showlegend=False, height=400)
            st.plotly_chart(fig_dwt, use_container_width=True)
        
        # Summary table
        st.dataframe(occ.style.format({
            "Total DWT": "{:,.0f}",
            "Avg Docking (h)": "{:.1f}"
        }), use_container_width=True)

with tab_dwt:
    st.subheader("DWT Analysis in Period")
    
    # Calculate initial DWT (vessels already in port at start)
    initial_dwt = proc_valid[
        (proc_valid["arrival_dt"] < current_dt) & 
        (proc_valid["departure_dt"] > current_dt)
    ]["DWT"].fillna(0).sum()
    
    # Collect all events (arrivals and departures) in period
    dwt_timeline = []
    
    for _, row in proc_valid.iterrows():
        if pd.notna(row['DWT']):
            if current_dt <= row['arrival_dt'] <= end_dt:
                dwt_timeline.append({
                    "Date": row['arrival_dt'],
                    "DWT": row['DWT'],
                    "Type": "Arrival",
                    "Vessel": row['SHIP']
                })
            if current_dt <= row['departure_dt'] <= end_dt:
                dwt_timeline.append({
                    "Date": row['departure_dt'],
                    "DWT": row['DWT'],
                    "Type": "Departure",
                    "Vessel": row['SHIP']
                })
    
    if dwt_timeline or initial_dwt > 0:
        if dwt_timeline:
            dwt_df = pd.DataFrame(dwt_timeline).sort_values("Date")
            
            # Calculate cumulative DWT correctly from initial state
            dwt_df["DWT_Change"] = dwt_df.apply(
                lambda x: x['DWT'] if x['Type'] == 'Arrival' else -x['DWT'],
                axis=1
            )
            dwt_df["DWT in Port"] = initial_dwt + dwt_df["DWT_Change"].cumsum()
            
            # Add initial point if there are events
            initial_point = pd.DataFrame([{
                'Date': current_dt,
                'DWT in Port': initial_dwt,
                'Type': 'Initial'
            }])
            
            dwt_plot = pd.concat([initial_point, dwt_df[['Date', 'DWT in Port', 'Type']]], ignore_index=True)
        else:
            # Only initial DWT, no events in period
            dwt_plot = pd.DataFrame([
                {'Date': current_dt, 'DWT in Port': initial_dwt, 'Type': 'Initial'},
                {'Date': end_dt, 'DWT in Port': initial_dwt, 'Type': 'Final'}
            ])
        
        # Chart
        fig_dwt_timeline = go.Figure()
        
        fig_dwt_timeline.add_trace(go.Scatter(
            x=dwt_plot['Date'],
            y=dwt_plot['DWT in Port'],
            mode='lines+markers',
            name='DWT in Port',
            line=dict(color='#06A77D', width=3),
            fill='tozeroy',
            hovertemplate='<b>%{x}</b><br>DWT: %{y:,.0f}<extra></extra>'
        ))
        
        fig_dwt_timeline.update_layout(
            title=f"DWT in Port Over Time (Initial: {initial_dwt:,.0f})",
            xaxis_title="Date",
            yaxis_title="Total DWT",
            height=400,
            hovermode='x unified'
        )
        
        st.plotly_chart(fig_dwt_timeline, use_container_width=True)
        
        # Statistics
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        col_s1.metric("Initial DWT", f"{initial_dwt:,.0f}")
        col_s2.metric("Average DWT", f"{dwt_plot['DWT in Port'].mean():,.0f}")
        col_s3.metric("Maximum DWT", f"{dwt_plot['DWT in Port'].max():,.0f}")
        col_s4.metric("Minimum DWT", f"{dwt_plot['DWT in Port'].min():,.0f}")
    else:
        st.info("No DWT data available for the selected period.")

# ---------- Detailed Tables ----------
st.markdown("---")
st.header("📋 Detailed Tables")

tab1, tab2, tab3 = st.tabs(["📍 Arrivals", "⚓ In Port", "🔄 Departures"])

with tab1:
    if arriving.empty:
        st.info("No arrivals in the period.")
    else:
        arriving_disp = arriving[["SHIP","arrival_dt","Berth","DWT","EstDockingTime"]].copy()
        arriving_disp = arriving_disp.rename(columns={
            "arrival_dt":"ETA",
            "EstDockingTime":"Est. Docking (h)"
        })
        arriving_disp["ETA"] = arriving_disp["ETA"].dt.strftime('%m/%d/%Y %H:%M')
        st.dataframe(arriving_disp.sort_values("ETA"), use_container_width=True, height=400)

with tab2:
    if in_port.empty:
        st.info("No vessels in port.")
    else:
        in_port_disp = in_port[["SHIP","arrival_dt","departure_dt","Berth","DWT","DockingTime","EstDockingTime"]].copy()
        in_port_disp = in_port_disp.rename(columns={
            "arrival_dt":"Arrival",
            "departure_dt":"ETD",
            "DockingTime":"Actual Docking (h)",
            "EstDockingTime":"Est. Docking (h)"
        })
        in_port_disp["Arrival"] = in_port_disp["Arrival"].dt.strftime('%m/%d/%Y %H:%M')
        in_port_disp["ETD"] = in_port_disp["ETD"].dt.strftime('%m/%d/%Y %H:%M')
        st.dataframe(in_port_disp.sort_values("Arrival"), use_container_width=True, height=400)

with tab3:
    if departing.empty:
        st.info("No departures in the period.")
    else:
        departing_disp = departing[["SHIP","departure_dt","Berth","DWT","DockingTime"]].copy()
        departing_disp = departing_disp.rename(columns={
            "departure_dt":"ETD",
            "DockingTime":"Actual Docking (h)"
        })
        departing_disp["ETD"] = departing_disp["ETD"].dt.strftime('%m/%d/%Y %H:%M')
        st.dataframe(departing_disp.sort_values("ETD"), use_container_width=True, height=400)

st.markdown("---")
st.caption("💡 Adjust the date range in the sidebar to analyze different periods.")