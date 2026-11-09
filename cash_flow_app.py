# ---------------------------------------------------------------
# Future Cash Flow Projector - a beginner-friendly Streamlit app
# ---------------------------------------------------------------
# This app estimates a company's FREE CASH FLOW for future years
# from a few simple assumptions, and (optionally) discounts those
# cash flows back to today's value.
#
# Free Cash Flow (FCF) formula used in this app:
#   EBIT            = Revenue x Operating Margin
#   NOPAT           = EBIT x (1 - Tax Rate)
#   FCF             = NOPAT + Depreciation - CapEx - Change in Working Capital
# ---------------------------------------------------------------

# SECTION 1: Import libraries
import streamlit as st      # builds the web page
import pandas as pd         # creates tables of numbers


# SECTION 2: The calculation function
def calculate_cash_flows(
    starting_revenue,
    growth_rate,
    years,
    operating_margin,
    tax_rate,
    depreciation_pct,
    capex_pct,
    nwc_pct,
    discount_rate,
):
    """
    Projects cash flows year by year.
    All percentages are passed in as decimals (10% -> 0.10).
    Returns a pandas table (DataFrame) with one row per year.
    """
    rows = []                          # one dictionary per year goes here
    previous_revenue = starting_revenue

    for year in range(1, years + 1):
        # Revenue grows by the growth rate each year
        revenue = previous_revenue * (1 + growth_rate)

        # Operating profit before taxes (EBIT)
        ebit = revenue * operating_margin

        # Profit after taxes (NOPAT). If EBIT is negative, no tax is charged.
        taxes = max(ebit, 0) * tax_rate
        nopat = ebit - taxes

        # Non-cash expense added back, and cash spent on equipment
        depreciation = revenue * depreciation_pct
        capex = revenue * capex_pct

        # Extra cash tied up as the business grows
        # (a % of the CHANGE in revenue)
        change_in_nwc = (revenue - previous_revenue) * nwc_pct

        # Free cash flow
        fcf = nopat + depreciation - capex - change_in_nwc

        # Present value: what this future cash is worth today
        discount_factor = 1 / ((1 + discount_rate) ** year)
        present_value = fcf * discount_factor

        rows.append(
            {
                "Year": year,
                "Revenue": revenue,
                "EBIT": ebit,
                "Taxes": taxes,
                "NOPAT": nopat,
                "Depreciation": depreciation,
                "CapEx": capex,
                "Change in NWC": change_in_nwc,
                "Free Cash Flow": fcf,
                "Present Value": present_value,
            }
        )

        previous_revenue = revenue     # this year's revenue starts next year

    return pd.DataFrame(rows)


def terminal_value(last_fcf, terminal_growth, discount_rate, years):
    """
    Estimates the value of all cash flows AFTER the forecast period
    (Gordon Growth method) and returns it in today's dollars.
    """
    tv = last_fcf * (1 + terminal_growth) / (discount_rate - terminal_growth)
    return tv / ((1 + discount_rate) ** years)


# SECTION 3: Page title and instructions
st.set_page_config(page_title="Cash Flow Projector", page_icon="💵")
st.title("💵 Future Cash Flow Projector")

st.write("Estimate a company's free cash flow for the next several years.")

st.subheader("How to use this app")
st.markdown(
    """
1. Enter the company's **current annual revenue** in the sidebar.
2. Fill in your **assumptions** (growth, margins, taxes, and so on).
3. The results update automatically on the right.
4. Check the table, chart, and totals at the bottom.

**Tip:** Not sure what to enter? Use the defaults to see how the app works,
then change one number at a time to see its effect.
"""
)

# SECTION 4: Sidebar inputs
st.sidebar.header("Company Information")

starting_revenue = st.sidebar.number_input(
    "Current annual revenue ($)", min_value=0.0, value=1_000_000.0, step=10_000.0
)

st.sidebar.header("Forecast Assumptions")

years = st.sidebar.slider("Years to forecast", min_value=1, max_value=15, value=5)

growth_pct = st.sidebar.number_input(
    "Annual revenue growth (%)", min_value=-50.0, max_value=200.0, value=8.0, step=0.5
)
margin_pct = st.sidebar.number_input(
    "Operating margin (%)", min_value=-100.0, max_value=100.0, value=15.0, step=0.5,
    help="Operating profit (EBIT) as a % of revenue.",
)
tax_pct = st.sidebar.number_input(
    "Tax rate (%)", min_value=0.0, max_value=100.0, value=25.0, step=0.5
)
dep_pct = st.sidebar.number_input(
    "Depreciation (% of revenue)", min_value=0.0, max_value=100.0, value=4.0, step=0.5,
    help="A non-cash expense that gets added back.",
)
capex_pct = st.sidebar.number_input(
    "Capital expenditures (% of revenue)", min_value=0.0, max_value=100.0, value=5.0, step=0.5,
    help="Cash spent on equipment, buildings, etc.",
)
nwc_pct = st.sidebar.number_input(
    "Working capital (% of revenue change)", min_value=0.0, max_value=100.0, value=10.0, step=0.5,
    help="Extra cash tied up in inventory and receivables as sales grow.",
)

st.sidebar.header("Valuation (Optional)")
discount_pct = st.sidebar.number_input(
    "Discount rate (%)", min_value=0.1, max_value=50.0, value=10.0, step=0.5,
    help="The return investors require. Used to find today's value of future cash.",
)
include_tv = st.sidebar.checkbox("Include terminal value", value=False)
terminal_pct = st.sidebar.number_input(
    "Terminal growth rate (%)", min_value=0.0, max_value=10.0, value=2.0, step=0.5,
    disabled=not include_tv,
)

# SECTION 5: Check inputs, then calculate
if starting_revenue <= 0:
    st.warning("Please enter a current revenue greater than zero.")
    st.stop()                      # stop here until the input is fixed

# Convert percentages to decimals (8% -> 0.08)
df = calculate_cash_flows(
    starting_revenue,
    growth_pct / 100,
    years,
    margin_pct / 100,
    tax_pct / 100,
    dep_pct / 100,
    capex_pct / 100,
    nwc_pct / 100,
    discount_pct / 100,
)

# SECTION 6: Show the results
st.header("Results")

total_fcf = df["Free Cash Flow"].sum()
total_pv = df["Present Value"].sum()

col1, col2 = st.columns(2)
col1.metric(f"Total FCF ({years} years)", f"${total_fcf:,.0f}")
col2.metric("Present value of FCF", f"${total_pv:,.0f}")

# Optional terminal value
if include_tv:
    if discount_pct <= terminal_pct:
        st.error("The discount rate must be higher than the terminal growth rate.")
    else:
        tv_pv = terminal_value(
            df["Free Cash Flow"].iloc[-1], terminal_pct / 100, discount_pct / 100, years
        )
        st.metric("Estimated enterprise value (PV of FCF + terminal value)",
                  f"${total_pv + tv_pv:,.0f}")
        st.caption(f"Terminal value (in today's dollars): ${tv_pv:,.0f}")

# Chart of free cash flow by year
st.subheader("Free Cash Flow by Year")
st.bar_chart(df.set_index("Year")["Free Cash Flow"])

# Detailed table
st.subheader("Detailed Projection")
money_columns = [c for c in df.columns if c != "Year"]
st.dataframe(
    df.style.format({c: "${:,.0f}" for c in money_columns}),
    hide_index=True,
    use_container_width=True,
)

# Let the user download the table as a CSV file
st.download_button(
    "Download table as CSV",
    df.to_csv(index=False),
    file_name="cash_flow_projection.csv",
    mime="text/csv",
)

st.caption(
    "This tool gives simple estimates for learning purposes. "
    "It is not financial advice."
)
