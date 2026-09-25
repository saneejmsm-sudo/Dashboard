import pandas as pd
import plotly.express as px
from dash import Dash, html, dcc, Input, Output, dash_table


# ============================================================
# 1. LOAD DATA
# ============================================================

DATA_FILE = "data/CIT308_LankaMart_Retail_Transactions.csv"

df = pd.read_csv(DATA_FILE)


# ============================================================
# 2. DATA TYPE CONVERSION
# ============================================================

# Convert date
df["order_date"] = pd.to_datetime(
    df["order_date"],
    errors="coerce"
)


# Convert numeric columns
numeric_columns = [
    "units",
    "unit_price_lkr",
    "discount_pct",
    "revenue_lkr",
    "cost_lkr",
    "profit_lkr",
    "delivery_days",
    "customer_rating"
]

for column in numeric_columns:
    df[column] = pd.to_numeric(
        df[column],
        errors="coerce"
    )


# ============================================================
# 3. DATA CLEANING
# ============================================================

# Remove exact duplicate records
df = df.drop_duplicates()


# Remove rows with invalid dates
df = df.dropna(subset=["order_date"])


# Clean text fields
text_columns = [
    "province",
    "city",
    "sales_channel",
    "customer_segment",
    "product_category",
    "product_name",
    "payment_method",
    "promotion"
]

for column in text_columns:
    df[column] = (
        df[column]
        .astype(str)
        .str.strip()
    )


# ------------------------------------------------------------
# STANDARDISE PRODUCT CATEGORY
# ------------------------------------------------------------

# Convert inconsistent category label "electronic"
# to the correct standard label "Electronics".
df["product_category"] = (
    df["product_category"]
    .replace({
        "electronic": "Electronics",
        "Electronic": "Electronics",
        "electronics": "Electronics"
    })
)


# ------------------------------------------------------------
# HANDLE MISSING CUSTOMER RATINGS
# ------------------------------------------------------------

# Replace missing customer ratings with the median rating.
median_rating = df["customer_rating"].median()

df["customer_rating"] = df["customer_rating"].fillna(
    median_rating
)


# ============================================================
# 4. CALCULATED FIELDS
# ============================================================

# Month field for monthly trend analysis
df["month"] = (
    df["order_date"]
    .dt.to_period("M")
    .astype(str)
)


# Profit margin percentage
df["profit_margin"] = (
    df["profit_lkr"]
    / df["revenue_lkr"].replace(0, pd.NA)
    * 100
)


# Delivery performance band
df["delivery_band"] = pd.cut(
    df["delivery_days"],
    bins=[-1, 2, 5, 100],
    labels=[
        "Fast (0-2 days)",
        "Standard (3-5 days)",
        "Slow (6+ days)"
    ]
)


# ============================================================
# 5. DASH APP
# ============================================================

app = Dash(__name__)

app.title = "LankaMart Dashboard"


# ============================================================
# 6. DROPDOWN OPTIONS
# ============================================================

province_options = [
    {"label": x, "value": x}
    for x in sorted(
        df["province"].dropna().unique()
    )
]


channel_options = [
    {"label": x, "value": x}
    for x in sorted(
        df["sales_channel"].dropna().unique()
    )
]


category_options = [
    {"label": x, "value": x}
    for x in sorted(
        df["product_category"].dropna().unique()
    )
]


# ============================================================
# 7. DASHBOARD LAYOUT
# ============================================================

app.layout = html.Div(
    [

        # ----------------------------------------------------
        # TITLE
        # ----------------------------------------------------

        html.Div(
            [
                html.H1(
                    "LankaMart Retail Performance Dashboard",
                    className="main-title"
                ),

                html.P(
                    "Interactive analysis of LankaMart retail "
                    "transactions for January to June 2026.",
                    className="subtitle"
                )
            ]
        ),


        # ----------------------------------------------------
        # FILTERS
        # ----------------------------------------------------

        html.Div(
            [

                # DATE FILTER
                html.Div(
                    [
                        html.Label("Date Range"),

                        dcc.DatePickerRange(
                            id="date-filter",

                            min_date_allowed=df[
                                "order_date"
                            ].min(),

                            max_date_allowed=df[
                                "order_date"
                            ].max(),

                            start_date=df[
                                "order_date"
                            ].min(),

                            end_date=df[
                                "order_date"
                            ].max(),

                            display_format="DD/MM/YYYY"
                        )
                    ],
                    className="filter-box"
                ),


                # PROVINCE FILTER
                html.Div(
                    [
                        html.Label("Province"),

                        dcc.Dropdown(
                            id="province-filter",

                            options=province_options,

                            value=[
                                x["value"]
                                for x in province_options
                            ],

                            multi=True,

                            placeholder="Select province..."
                        )
                    ],
                    className="filter-box"
                ),


                # SALES CHANNEL FILTER
                html.Div(
                    [
                        html.Label("Sales Channel"),

                        dcc.Dropdown(
                            id="channel-filter",

                            options=channel_options,

                            value=[
                                x["value"]
                                for x in channel_options
                            ],

                            multi=True,

                            placeholder="Select channel..."
                        )
                    ],
                    className="filter-box"
                ),


                # PRODUCT CATEGORY FILTER
                html.Div(
                    [
                        html.Label("Product Category"),

                        dcc.Dropdown(
                            id="category-filter",

                            options=category_options,

                            value=[
                                x["value"]
                                for x in category_options
                            ],

                            multi=True,

                            placeholder="Select category..."
                        )
                    ],
                    className="filter-box"
                ),


                # RESET BUTTON
                html.Button(
                    "Reset Filters",
                    id="reset-button",
                    n_clicks=0,
                    className="reset-button"
                )

            ],

            className="filters"
        ),


        # ----------------------------------------------------
        # STATUS
        # ----------------------------------------------------

        html.Div(
            id="filter-status",
            className="filter-status"
        ),


        # ----------------------------------------------------
        # KPI SECTION
        # ----------------------------------------------------

        html.H2("Key Performance Indicators"),


        html.Div(
            [

                html.Div(
                    [
                        html.H4("Total Revenue"),
                        html.H2(id="kpi-revenue")
                    ],
                    className="kpi-card"
                ),


                html.Div(
                    [
                        html.H4("Total Profit"),
                        html.H2(id="kpi-profit")
                    ],
                    className="kpi-card"
                ),


                html.Div(
                    [
                        html.H4("Profit Margin"),
                        html.H2(id="kpi-margin")
                    ],
                    className="kpi-card"
                ),


                html.Div(
                    [
                        html.H4("Return Rate"),
                        html.H2(id="kpi-return")
                    ],
                    className="kpi-card"
                )

            ],

            className="kpi-grid"
        ),


        # ----------------------------------------------------
        # ROW 1
        # ----------------------------------------------------

        html.Div(
            [

                html.Div(
                    dcc.Graph(id="monthly-chart"),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(id="category-chart"),
                    className="chart-card"
                )

            ],

            className="chart-row"
        ),


        # ----------------------------------------------------
        # ROW 2
        # ----------------------------------------------------

        html.Div(
            [

                html.Div(
                    dcc.Graph(id="province-chart"),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(id="channel-chart"),
                    className="chart-card"
                )

            ],

            className="chart-row"
        ),


        # ----------------------------------------------------
        # ROW 3
        # ----------------------------------------------------

        html.Div(
            [

                html.Div(
                    dcc.Graph(id="relationship-chart"),
                    className="chart-card"
                ),

                html.Div(
                    dcc.Graph(id="rating-chart"),
                    className="chart-card"
                )

            ],

            className="chart-row"
        ),


        # ----------------------------------------------------
        # MANAGEMENT INSIGHTS
        # ----------------------------------------------------

        html.Div(
            [

                html.H2("Management Insights & Actions"),

                html.Div(
                    id="insights",
                    className="insights-box"
                )

            ],

            className="insights-section"
        ),


        # ----------------------------------------------------
        # DETAILED TABLE
        # ----------------------------------------------------

        html.H2("Detailed Transaction View"),

        dash_table.DataTable(

            id="transaction-table",

            columns=[
                {"name": "Order ID", "id": "order_id"},
                {"name": "Date", "id": "order_date"},
                {"name": "Province", "id": "province"},
                {"name": "City", "id": "city"},
                {"name": "Channel", "id": "sales_channel"},
                {"name": "Segment", "id": "customer_segment"},
                {"name": "Category", "id": "product_category"},
                {"name": "Product", "id": "product_name"},
                {"name": "Units", "id": "units"},
                {"name": "Revenue (LKR)", "id": "revenue_lkr"},
                {"name": "Profit (LKR)", "id": "profit_lkr"},
                {"name": "Rating", "id": "customer_rating"},
                {"name": "Returned", "id": "returned"}
            ],

            data=[],

            page_size=10,

            sort_action="native",

            filter_action="native",

            style_table={
                "overflowX": "auto"
            },

            style_cell={
                "textAlign": "left",
                "padding": "8px",
                "fontFamily": "Arial",
                "fontSize": "13px"
            },

            style_header={
                "fontWeight": "bold"
            }

        )

    ],

    className="dashboard-container"
)


# ============================================================
# 8. CALLBACK
# ============================================================

@app.callback(

    Output("kpi-revenue", "children"),
    Output("kpi-profit", "children"),
    Output("kpi-margin", "children"),
    Output("kpi-return", "children"),

    Output("monthly-chart", "figure"),
    Output("category-chart", "figure"),
    Output("province-chart", "figure"),
    Output("channel-chart", "figure"),
    Output("relationship-chart", "figure"),
    Output("rating-chart", "figure"),

    Output("transaction-table", "data"),
    Output("filter-status", "children"),
    Output("insights", "children"),

    Input("date-filter", "start_date"),
    Input("date-filter", "end_date"),
    Input("province-filter", "value"),
    Input("channel-filter", "value"),
    Input("category-filter", "value"),
    Input("reset-button", "n_clicks")

)


def update_dashboard(
    start_date,
    end_date,
    selected_provinces,
    selected_channels,
    selected_categories,
    reset_clicks
):


    # --------------------------------------------------------
    # FILTER DATA
    # --------------------------------------------------------

    filtered = df.copy()


    # Date filter
    if start_date:
        filtered = filtered[
            filtered["order_date"]
            >= pd.to_datetime(start_date)
        ]


    # Date end filter
    if end_date:

        end_date_value = (
            pd.to_datetime(end_date)
            + pd.Timedelta(days=1)
        )

        filtered = filtered[
            filtered["order_date"]
            < end_date_value
        ]


    # Province filter
    if selected_provinces:
        filtered = filtered[
            filtered["province"]
            .isin(selected_provinces)
        ]


    # Sales channel filter
    if selected_channels:
        filtered = filtered[
            filtered["sales_channel"]
            .isin(selected_channels)
        ]


    # Product category filter
    if selected_categories:
        filtered = filtered[
            filtered["product_category"]
            .isin(selected_categories)
        ]


    # --------------------------------------------------------
    # EMPTY DATA PROTECTION
    # --------------------------------------------------------

    if filtered.empty:

        empty_figure = px.scatter(
            title="No data available for the selected filters"
        )

        return (

            "LKR 0",

            "LKR 0",

            "0.00%",

            "0.00%",

            empty_figure,

            empty_figure,

            empty_figure,

            empty_figure,

            empty_figure,

            empty_figure,

            [],

            "No transactions match the selected filters.",

            html.P(
                "Please change the filters to display results."
            )
        )


    # ========================================================
    # KPI CALCULATIONS
    # ========================================================

    total_revenue = filtered[
        "revenue_lkr"
    ].sum()


    total_profit = filtered[
        "profit_lkr"
    ].sum()


    margin = (

        total_profit
        / total_revenue
        * 100

        if total_revenue != 0
        else 0

    )


    return_rate = (

        (filtered["returned"] == "Yes").mean()
        * 100

    )


    # ========================================================
    # MONTHLY TREND
    # ========================================================

    monthly = (

        filtered

        .groupby(
            "month",
            as_index=False
        )

        .agg(
            Revenue=("revenue_lkr", "sum"),
            Profit=("profit_lkr", "sum")
        )

    )


    monthly_chart = px.line(

        monthly,

        x="month",

        y=[
            "Revenue",
            "Profit"
        ],

        markers=True,

        title="Monthly Revenue and Profit Trend"

    )


    monthly_chart.update_layout(

        xaxis_title="Month",

        yaxis_title="LKR"

    )


    # ========================================================
    # CATEGORY CHART
    # ========================================================

    category_data = (

        filtered

        .groupby(
            "product_category",
            as_index=False
        )

        ["revenue_lkr"]

        .sum()

        .sort_values(
            "revenue_lkr",
            ascending=True
        )

    )


    category_chart = px.bar(

        category_data,

        x="revenue_lkr",

        y="product_category",

        orientation="h",

        title="Revenue by Product Category"

    )


    category_chart.update_layout(

        xaxis_title="Revenue (LKR)",

        yaxis_title="Product Category"

    )


    # ========================================================
    # PROVINCE CHART
    # ========================================================

    province_data = (

        filtered

        .groupby(
            "province",
            as_index=False
        )

        ["revenue_lkr"]

        .sum()

        .sort_values(
            "revenue_lkr",
            ascending=False
        )

    )


    province_chart = px.bar(

        province_data,

        x="province",

        y="revenue_lkr",

        title="Revenue by Province"

    )


    province_chart.update_layout(

        xaxis_title="Province",

        yaxis_title="Revenue (LKR)"

    )


    # ========================================================
    # SALES CHANNEL
    # ========================================================

    channel_data = (

        filtered

        .groupby(
            "sales_channel",
            as_index=False
        )

        .agg(

            Revenue=("revenue_lkr", "sum"),

            Profit=("profit_lkr", "sum")

        )

    )


    channel_chart = px.bar(

        channel_data,

        x="sales_channel",

        y=[
            "Revenue",
            "Profit"
        ],

        barmode="group",

        title="Revenue and Profit by Sales Channel"

    )


    channel_chart.update_layout(

        xaxis_title="Sales Channel",

        yaxis_title="LKR"

    )


    # ========================================================
    # REVENUE VS PROFIT
    # ========================================================

    relationship_data = (

        filtered

        .groupby(
            "product_category",
            as_index=False
        )

        .agg(

            Revenue=("revenue_lkr", "sum"),

            Profit=("profit_lkr", "sum"),

            Units=("units", "sum")

        )

    )


    relationship_chart = px.scatter(

        relationship_data,

        x="Revenue",

        y="Profit",

        size="Units",

        color="product_category",

        hover_name="product_category",

        title="Revenue vs Profit by Product Category"

    )


    relationship_chart.update_layout(

        xaxis_title="Revenue (LKR)",

        yaxis_title="Profit (LKR)"

    )


    # ========================================================
    # CUSTOMER RATING
    # ========================================================

    rating_data = (

        filtered

        .groupby(
            "customer_rating"
        )

        .size()

        .reset_index(
            name="Transactions"
        )

    )


    rating_chart = px.bar(

        rating_data,

        x="customer_rating",

        y="Transactions",

        title="Customer Rating Distribution"

    )


    rating_chart.update_layout(

        xaxis_title="Customer Rating",

        yaxis_title="Number of Transactions"

    )


    # ========================================================
    # TABLE
    # ========================================================

    table_data = filtered.copy()


    table_data["order_date"] = (

        table_data["order_date"]

        .dt.strftime("%Y-%m-%d")

    )


    table_columns = [

        "order_id",

        "order_date",

        "province",

        "city",

        "sales_channel",

        "customer_segment",

        "product_category",

        "product_name",

        "units",

        "revenue_lkr",

        "profit_lkr",

        "customer_rating",

        "returned"

    ]


    table_data = table_data[
        table_columns
    ].copy()


    table_data = table_data.round(2)


    table_records = table_data.to_dict(
        "records"
    )


    # ========================================================
    # FILTER STATUS
    # ========================================================

    status = (

        f"Showing {len(filtered):,} transactions "

        f"from "
        f"{filtered['order_date'].min().strftime('%d %b %Y')} "

        f"to "
        f"{filtered['order_date'].max().strftime('%d %b %Y')}"

    )


    # ========================================================
    # MANAGEMENT INSIGHTS
    # ========================================================

    top_province = (

        province_data.iloc[0]["province"]

        if not province_data.empty

        else "N/A"

    )


    top_province_revenue = (

        province_data.iloc[0]["revenue_lkr"]

        if not province_data.empty

        else 0

    )


    top_category = (

        category_data

        .sort_values(
            "revenue_lkr",
            ascending=False
        )

        .iloc[0]["product_category"]

        if not category_data.empty

        else "N/A"

    )


    top_channel = (

        channel_data

        .sort_values(
            "Profit",
            ascending=False
        )

        .iloc[0]["sales_channel"]

        if not channel_data.empty

        else "N/A"

    )


    insights = html.Div(

        [

            html.P(
                [
                    html.Strong(
                        "1. Highest revenue province: "
                    ),

                    f"{top_province}, generating approximately "
                    f"LKR {top_province_revenue:,.0f} "
                    f"in revenue."
                ]
            ),


            html.P(
                [
                    html.Strong(
                        "2. Leading product category: "
                    ),

                    f"{top_category} based on revenue "
                    f"within the selected data."
                ]
            ),


            html.P(
                [
                    html.Strong(
                        "3. Strongest channel by profit: "
                    ),

                    f"{top_channel}. Management should monitor "
                    f"this channel and identify practices that "
                    f"support its profitability."
                ]
            ),


            html.P(
                [
                    html.Strong(
                        "4. Action: "
                    ),

                    "Use the filters to investigate "
                    "lower-performing provinces, categories "
                    "and channels before making resource "
                    "allocation decisions."
                ]
            )

        ]

    )


    # ========================================================
    # RETURN ALL OUTPUTS
    # ========================================================

    return (

        f"LKR {total_revenue:,.0f}",

        f"LKR {total_profit:,.0f}",

        f"{margin:.2f}%",

        f"{return_rate:.2f}%",

        monthly_chart,

        category_chart,

        province_chart,

        channel_chart,

        relationship_chart,

        rating_chart,

        table_records,

        status,

        insights

    )


# ============================================================
# 9. RUN APP
# ============================================================

if __name__ == "__main__":
    app.run(debug=True)