import streamlit as st
import yfinance as yf
import pandas as pd
import altair as alt

# codex-update: 2026-03-09 fast-theme-toggle + no-table-index
st.set_page_config(layout="wide")

if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = True

def toggle_theme():
    st.session_state.dark_mode = not st.session_state.dark_mode

_, mode_col_right = st.columns([8, 2])
with mode_col_right:
    st.button(
        "Switch to Light Mode" if st.session_state.dark_mode else "Switch to Dark Mode",
        use_container_width=True,
        on_click=toggle_theme,
    )

if st.session_state.dark_mode:
    chart_bg = "#111827"
    chart_line = "#60a5fa"
    chart_grid = "#374151"
    chart_text = "#f3f4f6"
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #0f1117;
                color: #f2f5fa;
            }
            [data-testid="stHeader"] {
                background: #0f1117;
            }
            [data-testid="stToolbar"] {
                background: #0f1117;
            }
            [data-testid="stDecoration"] {
                background: #0f1117;
            }
            .block-container {
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }
            .summary-table table {
                width: 100%;
                border-collapse: collapse;
            }
            .summary-table {
                max-width: 1180px;
                margin: 0 auto;
                font-size: 1.5rem;
            }
            .summary-table th, .summary-table td {
                padding: 0.6rem 0.8rem;
                border: 1px solid #2a2f3a;
                text-align: left;
            }
            .section-gap {
                height: 1.75rem;
            }
            .stButton > button {
                background-color: #1f2937;
                color: #f9fafb;
                border: 1px solid #374151;
            }
            .stButton > button:hover {
                background-color: #111827;
                color: #ffffff;
                border: 1px solid #4b5563;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
else:
    chart_bg = "#ffffff"
    chart_line = "#1d4ed8"
    chart_grid = "#e5e7eb"
    chart_text = "#111827"
    st.markdown(
        """
        <style>
            .stApp {
                background-color: #ffffff;
                color: #111827;
            }
            .block-container {
                padding-left: 1.25rem;
                padding-right: 1.25rem;
            }
            .summary-table table {
                width: 100%;
                border-collapse: collapse;
            }
            .summary-table {
                max-width: 1180px;
                margin: 0 auto;
                font-size: 1.5rem;
            }
            .summary-table th, .summary-table td {
                padding: 0.6rem 0.8rem;
                border: 1px solid #d9dde7;
                text-align: left;
            }
            .section-gap {
                height: 1.75rem;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

# Define symbols
symbols = {
    'USDBRL': 'USDBRL=X',
    'Bitcoin': 'BTC-USD',
    'Gold': 'GC=F',
    'Ibovespa': '^BVSP',
    'S&P 500': '^GSPC'
}

# Function to get data
if hasattr(st, "cache_data"):
    @st.cache_data(ttl=900, show_spinner=False)
    def get_data(symbol, period='2y'):
        data = yf.download(symbol, period=period)
        return data
else:
    @st.cache(ttl=900, show_spinner=False)
    def get_data(symbol, period='2y'):
        data = yf.download(symbol, period=period)
        return data

# Get current price and changes
def get_summary(data):
    try:
        if len(data) == 0 or data['Close'].empty:
            return float('nan'), float('nan'), float('nan'), float('nan')
        current = float(data['Close'].iloc[-1])
        daily_change = float(data['Close'].pct_change().iloc[-1] * 100) if len(data) > 1 else float('nan')
        # Monthly: approx 30 days
        if len(data) > 30:
            monthly_change = float((data['Close'].iloc[-1] / data['Close'].iloc[-30] - 1) * 100)
        else:
            monthly_change = float('nan')
        # Yearly: approx 365 days
        if len(data) > 365:
            yearly_change = float((data['Close'].iloc[-1] / data['Close'].iloc[-365] - 1) * 100)
        else:
            yearly_change = float('nan')
        return current, daily_change, monthly_change, yearly_change
    except Exception:
        return float('nan'), float('nan'), float('nan'), float('nan')

summary_data = []
plot_data = []

for name, symbol in symbols.items():
    data = get_data(symbol)
    current, daily, monthly, yearly = get_summary(data)
    formatted_current = f"{current:.2f}" if not pd.isna(current) else 'N/A'
    formatted_daily = f"{daily:.2f}%" if not pd.isna(daily) else 'N/A'
    formatted_monthly = f"{monthly:.2f}%" if not pd.isna(monthly) else 'N/A'
    formatted_yearly = f"{yearly:.2f}%" if not pd.isna(yearly) else 'N/A'
    summary_data.append([name, formatted_current, formatted_daily, formatted_monthly, formatted_yearly])
    
    # Plot
    if not data.empty:
        plot_data.append((name, data['Close']))

# Layout
df = pd.DataFrame(summary_data, columns=['Index', 'Current Price', 'Daily Change %', 'Monthly Change %', 'Yearly Change %'])
_, center_col, _ = st.columns([0.7, 8.6, 0.7])
with center_col:
    st.markdown(
        f'<div class="summary-table">{df.to_html(index=False)}</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="section-gap"></div>', unsafe_allow_html=True)

    plot_cols = st.columns(2)
    for i, (name, close_series) in enumerate(plot_data):
        with plot_cols[i % 2]:
            st.markdown(f"<div style='font-size: 1.4rem; font-weight: 700; margin-bottom: 0.35rem;'>{name}</div>", unsafe_allow_html=True)
            chart_df = close_series.reset_index()
            chart_df.columns = ["Date", "Price"]
            chart = (
                alt.Chart(chart_df)
                .mark_line(color=chart_line)
                .encode(
                    x=alt.X("Date:T", title=None),
                    y=alt.Y("Price:Q", title=None),
                    tooltip=[
                        alt.Tooltip("Date:T", title="Date"),
                        alt.Tooltip("Price:Q", title="Price", format=".2f"),
                    ],
                )
                .properties(height=420, background=chart_bg)
                .interactive()
                .configure_view(strokeOpacity=0)
                .configure_axis(
                    labelColor=chart_text,
                    titleColor=chart_text,
                    gridColor=chart_grid,
                    labelFontSize=16,
                    titleFontSize=16,
                )
                .configure_legend(
                    labelFontSize=16,
                    titleFontSize=16,
                    labelColor=chart_text,
                    titleColor=chart_text,
                )
            )
            st.altair_chart(chart, use_container_width=True)

# Note: To run this script, use: streamlit run dashboard.py
