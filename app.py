
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import numpy as np

# Page configuration
st.set_page_config(
    page_title="Sales Performance & Customer Insights",
    page_icon="📊",
    layout="wide"
)

# Load cleaned fact table
fact_sales = pd.read_csv(
    "data/cleaned_datasets/fact_sales_clean.csv"
)

fact_sales['order_datetime'] = pd.to_datetime(
    fact_sales['order_datetime'],
    errors='coerce'
)

# Dashboard title
st.title("Sales Performance & Customer Insights")
st.caption("Sales Analysis | Python Capstone")

st.markdown(
    """
    <div style="
        background-color: lightsteelblue;
        color: #1f2937;
        padding: 15px 20px;
        border-radius: 8px;
        font-size: 16px;
    ">
        Sales data loaded successfully.
    </div>
    """,
    unsafe_allow_html=True
)

# Dashboard Filters
st.subheader("Dashboard Filters")

date_min = fact_sales['order_datetime'].min().date()
date_max = fact_sales['order_datetime'].max().date()

region_options = sorted(
    r for r in fact_sales['region_name'].dropna().unique()
    if r != "Unknown"
)

category_options = sorted(
    c for c in fact_sales['category'].dropna().unique()
    if c != "Unknown"
)

col1, col2, col3 = st.columns(3)

with col1:
    selected_dates = st.date_input(
        "Date Range",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max
    )

with col2:
    selected_region = st.multiselect(
        "Region",
        options=["Unknown"] + region_options,
        default=["Unknown"] + region_options
    )

with col3:
    selected_category = st.multiselect(
        "Category",
        options=["Unknown"] + category_options,
        default=["Unknown"] + category_options
    )

# Extract selected date range
if len(selected_dates) == 2:
    start_date, end_date = selected_dates
elif len(selected_dates) == 1:
    start_date = selected_dates[0]
    end_date = selected_dates[0]
else:
    start_date = date_min
    end_date = date_max

# Filter data
filtered_sales = fact_sales.copy()

# Region filter
if "Unknown" in selected_region:
    filtered_sales = filtered_sales[
        filtered_sales['region_name'].isna() |
        (filtered_sales['region_name'] == "Unknown") |
        filtered_sales['region_name'].isin(
            [r for r in selected_region if r != "Unknown"]
        )
    ]
else:
    filtered_sales = filtered_sales[
        filtered_sales['region_name'].isin(selected_region)
    ]

# Category filter
if "Unknown" in selected_category:
    filtered_sales = filtered_sales[
        filtered_sales['category'].isna() |
        (filtered_sales['category'] == "Unknown") |
        filtered_sales['category'].isin(
            [c for c in selected_category if c != "Unknown"]
        )
    ]
else:
    filtered_sales = filtered_sales[
        filtered_sales['category'].isin(selected_category)
    ]

    # Date filter
filtered_sales = filtered_sales[
    (filtered_sales['order_datetime'].dt.date >= start_date) &
    (filtered_sales['order_datetime'].dt.date <= end_date)
].copy()

# Calculate revenue
filtered_sales['Total_Revenue'] = (
    filtered_sales['quantity'] *
    filtered_sales['unit_price_at_purchase']
)

total_revenue = filtered_sales['Total_Revenue'].sum()
total_orders = filtered_sales['order_id'].nunique()

average_order_value = (
    total_revenue / total_orders
    if total_orders > 0 else 0
)


# KPI Section
st.divider()

st.subheader("Sales Performance Overview")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric(
        "Total Revenue",
        f"₱{total_revenue:,.2f}"
    )

with col2:
    st.metric(
        "Total Orders",
        f"{total_orders:,.0f}"
    )

with col3:
    st.metric(
        "Average Order Value",
        f"₱{average_order_value:,.2f}"
    )

st.divider()

# BQ4 and BQ5: Sales Performance

col1, col2 = st.columns(2)

with col1:
    # BQ4: Monthly Revenue Trend
    st.subheader("Monthly Revenue Trend")

    bq4 = (
        filtered_sales
        .dropna(subset=['order_datetime'])
        .assign(
            month=lambda df: df['order_datetime'].dt.to_period('M')
        )
        .groupby('month')['Total_Revenue']
        .sum()
        .reset_index()
    )

    bq4['month'] = bq4['month'].dt.to_timestamp()


    fig = go.Figure()

    fig.add_trace(go.Scatter(
        x=bq4['month'],
        y=bq4['Total_Revenue'],
        mode='lines+markers',
        name='Monthly Revenue',
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.15)',
        line=dict(width=2),
        marker=dict(size=6)
    ))

    fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
            xaxis=dict(
            title='Month',
            tickformat='%b %Y',
            dtick='M1',
            tickangle=-45,
            showgrid=False,
            fixedrange=True
        ),
            yaxis=dict(
            title='Revenue (₱)',
            range=[0, 500000],
            dtick=100000,
            tickformat=',.0f',
            showgrid=False,
            fixedrange=True
),
            hovermode='x unified',
            height=300,
            margin=dict(l=20, r=20, t=30, b=60)
    )

    st.plotly_chart(
        fig,
        use_container_width=True,
        config={'scrollZoom': False}
    )

with col2:
    # BQ5: Top 10 Products by Revenue
    st.subheader("Top 10 Products by Revenue")

    bq5 = (
        filtered_sales[
            filtered_sales['product_id'] != 'PROD00000'
        ]
        .groupby('product_id')['Total_Revenue']
        .sum()
        .reset_index()
        .sort_values(
            by='Total_Revenue',
            ascending=False
        )
        .head(10)
    )

    bq5_chart = bq5.sort_values(
        by='Total_Revenue',
        ascending=True
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bq5_chart['Total_Revenue'],
        y=bq5_chart['product_id'],
        orientation='h',
        text=bq5_chart['Total_Revenue'].apply(
            lambda x: f'₱{x:,.2f}'
        ),
        textposition='outside',
        marker=dict(color='steelblue')
    ))

    fig.update_layout(
        xaxis=dict(
            title=None,
            showticklabels=False,
            range=[
                0,
                bq5_chart['Total_Revenue'].max() * 1.25
                if not bq5_chart.empty else 1
            ],
            fixedrange=True
        ),
        yaxis=dict(
            title='Product ID',
            fixedrange=True
        ),
        height=300,
        margin=dict(l=20, r=80, t=30, b=20),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# BQ6 and BQ7: Revenue Breakdown

col1, col2 = st.columns(2)

with col1:
    # BQ6: Revenue by Category
    st.subheader("Revenue by Category")

    bq6_data = filtered_sales.copy()
    bq6_data['category'] = bq6_data['category'].fillna('Unknown')

    bq6 = (
        bq6_data
        .groupby('category')['Total_Revenue']
        .sum()
        .reset_index()
        .sort_values(
            by='Total_Revenue',
            ascending=False
        )
    )

    bq6_chart = bq6.sort_values(
        by='Total_Revenue',
        ascending=True
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bq6_chart['Total_Revenue'],
        y=bq6_chart['category'],
        orientation='h',
        text=bq6_chart['Total_Revenue'].apply(
            lambda x: f'₱{x:,.2f}'
        ),
        textposition='outside',
        marker=dict(color='steelblue')
    ))

    fig.update_layout(
        xaxis=dict(
            title=None,
            showticklabels=False,
            range=[
                0,
                bq6_chart['Total_Revenue'].max() * 1.25
                if not bq6_chart.empty else 1
            ],
            fixedrange=True
        ),
        yaxis=dict(
            title=None,
            fixedrange=True
        ),
        height=400,
        margin=dict(l=20, r=100, t=30, b=20),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

with col2:
    # BQ7: Revenue by Region
    st.subheader("Revenue by Region")

    bq7 = (
        filtered_sales
        .groupby('region_name')['Total_Revenue']
        .sum()
        .reset_index()
        .sort_values(
            by='Total_Revenue',
            ascending=True
        )
    )

    fig = go.Figure()

    fig.add_trace(go.Bar(
        x=bq7['Total_Revenue'],
        y=bq7['region_name'],
        orientation='h',
        text=bq7['Total_Revenue'].apply(
            lambda x: f'₱{x:,.2f}'
        ),
        textposition='outside',
        marker=dict(color='steelblue')
    ))

    fig.update_layout(
        xaxis=dict(
            title=None,
            showticklabels=False,
            range=[
                0,
                bq7['Total_Revenue'].max() * 1.25
                if not bq7.empty else 1
            ],
            fixedrange=True
        ),
        yaxis=dict(
            title=None,
            fixedrange=True
        ),
        height=400,
        margin=dict(l=20, r=100, t=30, b=20),
        showlegend=False
    )

    st.plotly_chart(fig, use_container_width=True)

# BQ8: New vs Repeat Customers
st.subheader("New vs Repeat Customers")

customer_data = filtered_sales[
    filtered_sales['customer_id'] != 'CUST999999'
]

customer_orders = (
    customer_data
    .groupby('customer_id')['order_id']
    .nunique()
    .reset_index(name='order_count')
)

customer_orders['customer_type'] = np.where(
    customer_orders['order_count'] >= 2,
    'Repeat',
    'New'
)

bq8 = (
    customer_orders
    .groupby('customer_type')['customer_id']
    .count()
    .reset_index(name='customer_count')
)

total_customers = bq8['customer_count'].sum()

col1, col2 = st.columns(2)

for col, customer_type in zip(
    [col1, col2],
    ['New', 'Repeat']
):
    customer_row = bq8[
        bq8['customer_type'] == customer_type
    ]

    value = (
        customer_row['customer_count'].iloc[0]
        if not customer_row.empty else 0
    )

    percentage = (
        value / total_customers * 100
        if total_customers > 0 else 0
    )

    with col:
        fig = go.Figure(go.Indicator(
            mode="gauge+number",
            value=percentage,
            title={'text': customer_type + " Customers"},
            number={'suffix': "%"},
            gauge={
                'axis': {
                'range': [0, 100],
                'tickcolor': '#E5E7EB'
        },
                'bar': {'color': '#4682B4'},
                'bgcolor': '#B0C4DE',
                'borderwidth': 0
}
        ))

        fig.update_layout(
            height=300,
            margin=dict(l=20, r=20, t=60, b=20),
            paper_bgcolor='#111827',
            font=dict(color='#E5E7EB')
)

        st.plotly_chart(
            fig,
            use_container_width=True
        )
# BQ9: Customer Spending Distribution

customer_spending = (
    filtered_sales[
        filtered_sales['customer_id'] != 'CUST999999'
    ]
    .groupby('customer_id')['Total_Revenue']
    .sum()
    .reset_index(name='Customer_Spending')
)

st.subheader("Customer Spending Distribution")

fig = go.Figure()

fig.add_trace(go.Histogram(
    x=customer_spending['Customer_Spending'],
    nbinsx=30,
    marker=dict(color='#4682B4'),
    name='Customers'
))

fig.update_layout(
    xaxis=dict(
        title='Total Customer Spending (₱)',
        showgrid=False
    ),
    yaxis=dict(
        title='Number of Customers',
        showgrid=False
    ),
    height=350,
    showlegend=False,
    paper_bgcolor='#111827',
    plot_bgcolor='#111827',
    font=dict(color='#E5E7EB')
)

st.plotly_chart(
    fig,
    use_container_width=True
)

# BQ10: Monthly Cancellations Trend

cancellations = (
    filtered_sales[
        filtered_sales['order_status'] == 'Cancelled'
    ]
    .groupby(
        filtered_sales['order_datetime'].dt.to_period('M')
    )['order_id']
    .nunique()
    .reset_index(name='Cancelled_Orders')
)

cancellations['order_datetime'] = (
    cancellations['order_datetime'].dt.to_timestamp()
)

st.subheader("Monthly Cancellations Trend")

fig = go.Figure()

fig.add_trace(go.Scatter(
    x=cancellations['order_datetime'],
    y=cancellations['Cancelled_Orders'],
    mode='lines+markers',
    name='Cancelled Orders',
    line=dict(color='#4682B4', width=2),
    marker=dict(size=6)
))

fig.update_layout(
    xaxis=dict(
        title='Month',
        tickformat='%b %Y',
        showgrid=False
    ),
    yaxis=dict(
        title='Number of Cancelled Orders',
        showgrid=False
    ),
    height=350,
    paper_bgcolor='#111827',
    plot_bgcolor='#111827',
    font=dict(color='#E5E7EB'),
    showlegend=False
)

st.plotly_chart(
    fig,
    use_container_width=True
)


# Filter Summary
st.divider()

st.caption(
    f"Filtered records: {len(filtered_sales):,} "
    f"| Selected period: {start_date} to {end_date}"
)
