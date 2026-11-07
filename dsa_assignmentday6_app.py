import streamlit as st
import pandas as pd
import plotly.express as px

print("Libraries imported successfully")

st.set_page_config(
    page_title="Retail Sales Dashboard",
    layout="wide"
)

st.title("Retail Sales Dashboard")
st.caption("Sales Performance and Customer Insights")

print("LOADING RETAIL DATA")
print("=" * 50)

sales = pd.read_csv(
    "data/cleaned_datasets/fact_sales_clean.csv"
)

sales["order_datetime"] = pd.to_datetime(
    sales["order_datetime"],
    errors="coerce"
)

sales["month"] = sales["order_datetime"].dt.strftime("%Y-%m")

print("Dataset loaded successfully")
print("Rows:", len(sales))
print("Columns:", len(sales.columns))

fulfilled = sales[
    sales["order_status"].isin(["Completed", "Shipped"])
].copy()

print("Fulfilled records:", len(fulfilled))
print("Fulfilled orders:", fulfilled["order_id"].nunique())

st.sidebar.header("Dashboard Filters")

# Month Filter
month_options = sorted(fulfilled["month"].dropna().unique())

selected_month = st.sidebar.multiselect(
    "Select Month",
    month_options,
    default=month_options
)

# Region Filter
region_options = sorted(fulfilled["region_name"].dropna().unique())

selected_region = st.sidebar.multiselect(
    "Select Region",
    region_options,
    default=region_options
)

# Sales Channel Filter
channel_options = sorted(fulfilled["sales_channel"].dropna().unique())

selected_channel = st.sidebar.multiselect(
    "Select Sales Channel",
    channel_options,
    default=channel_options
)

filtered_sales = fulfilled.copy()

filtered_sales = filtered_sales[
    filtered_sales["month"].isin(selected_month)
]

filtered_sales = filtered_sales[
    filtered_sales["region_name"].isin(selected_region)
]

filtered_sales = filtered_sales[
    filtered_sales["sales_channel"].isin(selected_channel)
]

print("Filtered records:", len(filtered_sales))

st.write("Dashboard is running!")
st.write("Filtered records:", len(filtered_sales))

print("DASHBOARD KPI CALCULATIONS")
print("=" * 50)



# Calculate Total Revenue
filtered_sales["Total_Revenue"] = (
    filtered_sales["quantity"] *
    filtered_sales["unit_price_at_purchase"]
)

# Total Sales
total_sales = filtered_sales["Total_Revenue"].sum()

# Total Orders
total_orders = filtered_sales["order_id"].nunique()

# Average Order Value
average_order_value = total_sales / total_orders if total_orders > 0 else 0

# Top Category
category_sales = (
    filtered_sales.groupby("category")["Total_Revenue"]
    .sum()
    .sort_values(ascending=False)
)

if len(category_sales) > 0:
    top_category = category_sales.index[0]
else:
    top_category = "N/A"

# Display KPI Cards
st.subheader("Sales Performance Overview")

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Sales", f"₱{total_sales:,.2f}")

with col2:
    st.metric("Total Orders", f"{total_orders:,}")

with col3:
    st.metric("Average Order Value", f"₱{average_order_value:,.2f}")

with col4:
    st.metric("Top Category", top_category)




    print("MONTHLY SALES TREND")
print("=" * 50)

# Group sales by month
monthly_sales = (
    filtered_sales.groupby("month")["Total_Revenue"]
    .sum()
    .reset_index()
)

# Create line chart
fig = px.line(
    monthly_sales,
    x="month",
    y="Total_Revenue",
    title="Monthly Sales Trend",
    markers=True,
    labels={
        "month": "Month",
        "Total_Revenue": "Total Sales (PHP)"
    }
)

# Display chart
st.subheader("Monthly Sales Trend")
st.plotly_chart(fig, use_container_width=True)


print("SALES BY PRODUCT CATEGORY")
print("=" * 50)

# Group sales by category
category_sales = (
    filtered_sales.groupby("category")["Total_Revenue"]
    .sum()
    .reset_index()
)

# Sort sales from lowest to highest
category_sales = category_sales.sort_values(
    by="Total_Revenue",
    ascending=True
)

# Create horizontal bar chart
fig = px.bar(
    category_sales,
    x="Total_Revenue",
    y="category",
    orientation="h",
    title="Sales by Product Category",
    labels={
        "Total_Revenue": "Total Sales (PHP)",
        "category": "Product Category"
    },
    hover_data={
        "Total_Revenue": ":,.2f"
    }
)

# Display chart
st.subheader("Sales by Product Category")
st.plotly_chart(fig, use_container_width=True)


print("SALES BY REGION")
print("=" * 50)

# Group sales by region
region_sales = (
    filtered_sales.groupby("region_name")["Total_Revenue"]
    .sum()
    .reset_index()
)

# Sort sales
region_sales = region_sales.sort_values(
    by="Total_Revenue",
    ascending=True
)

# Create bar chart
fig = px.bar(
    region_sales,
    x="Total_Revenue",
    y="region_name",
    orientation="h",
    title="Sales by Region",
    labels={
        "Total_Revenue": "Total Sales (PHP)",
        "region_name": "Region"
    },
    hover_data={
        "Total_Revenue": ":,.2f"
    }
)

# Display chart
st.subheader("Sales by Region")
st.plotly_chart(fig, use_container_width=True)



print("FILTERED SALES DETAIL")
print("=" * 50)

st.divider()
st.subheader("Filtered Sales Details")

# Select columns to display
display_columns = [
    "order_id",
    "order_datetime",
    "product_id",
    "category",
    "quantity",
    "unit_price_at_purchase",
    "region_name",
    "sales_channel",
    "Total_Revenue"
]

# Create detail table
sales_details = filtered_sales[display_columns].copy()

# Display table
st.dataframe(
    sales_details,
    use_container_width=True,
    hide_index=True
)

print("Displayed records:", len(sales_details))


st.divider()

st.header("Business Questions and Key Findings")

# Question 1
st.subheader("1. Which product category generates the highest sales?")

if not category_sales.empty:
    highest_category = category_sales.iloc[0]["category"]
    highest_sales = category_sales.iloc[0]["Total_Revenue"]

    st.write(
        f"{highest_category} generates the highest sales "
        f"with PHP {highest_sales:,.2f}."
    )

# Question 2
st.subheader("2. Which region contributes the most to sales?")

if not region_sales.empty:
    highest_region = region_sales.iloc[-1]["region_name"]
    highest_region_sales = region_sales.iloc[-1]["Total_Revenue"]

    st.write(
        f"{highest_region} records the highest sales "
        f"with PHP {highest_region_sales:,.2f}."
    )

# Question 3
st.subheader("3. What is the monthly sales performance?")

if not monthly_sales.empty:
    highest_month = monthly_sales.loc[
        monthly_sales["Total_Revenue"].idxmax()
    ]

    st.write(
        f"{highest_month['month']} records the highest monthly sales "
        f"with PHP {highest_month['Total_Revenue']:,.2f}."
    )

# Question 4
st.subheader("4. Which sales channel generates the highest sales?")

channel_sales = (
    filtered_sales.groupby("sales_channel")["Total_Revenue"]
    .sum()
    .reset_index()
    .sort_values(by="Total_Revenue", ascending=False)
)

if not channel_sales.empty:
    highest_channel = channel_sales.iloc[0]["sales_channel"]
    highest_channel_sales = channel_sales.iloc[0]["Total_Revenue"]

    st.write(
        f"{highest_channel} generates the highest sales "
        f"with PHP {highest_channel_sales:,.2f}."
    )