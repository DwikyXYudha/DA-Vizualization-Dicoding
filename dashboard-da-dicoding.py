import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import streamlit as st
from babel.numbers import format_currency

sns.set(style='dark')

all_data = pd.read_csv("all_data.csv")


def create_daily_orders_df(df):
    daily_orders_df = df.resample(rule='D', on='order_purchase_timestamp').agg({
        "order_id": "nunique",
        "price": "sum"
    })
    daily_orders_df = daily_orders_df.reset_index()
    daily_orders_df.rename(columns={
        "order_id": "order_count",
        "price": "revenue"
    }, inplace=True)

    return daily_orders_df


def create_category_sales(df):
    category_sales = all_data.groupby('product_category_name')['order_item_id'].sum().sort_values(ascending=False).reset_index()
    return category_sales

def create_top_5_states_df(df):
    top_5_states_df = df.groupby(by='customer_state').customer_id.nunique().sort_values(
        ascending=False).reset_index().head(5)
    return top_5_states_df


def create_rfm_df(df):
    rfm_df = df.groupby(by="customer_id", as_index=False).agg({
        "order_purchase_timestamp": "max",  # max_order_timestamp
        "order_id": "nunique",  # frequency
        "price": "sum"  # monetary
    })
    rfm_df.columns = ["customer_id", "max_order_timestamp", "frequency", "monetary"]

    rfm_df["max_order_timestamp"] = rfm_df["max_order_timestamp"].dt.date
    recent_date = df["order_purchase_timestamp"].dt.date.max()
    rfm_df["recency"] = rfm_df["max_order_timestamp"].apply(lambda x: (recent_date - x).days)  # days

    return rfm_df

all_data.sort_values(by="order_purchase_timestamp", inplace=True)
all_data.reset_index(inplace=True)

all_data["order_purchase_timestamp"] = pd.to_datetime(all_data["order_purchase_timestamp"])

min_date = all_data["order_purchase_timestamp"].min()
max_date = all_data["order_purchase_timestamp"].max()

with st.sidebar:
    start_date, end_date = st.date_input(
        label='Time Range',
        min_value=min_date,
        max_value=max_date,
        value=[min_date, max_date]
    )

main_df = all_data[
    (all_data["order_purchase_timestamp"] >= str(start_date)) &
    (all_data["order_purchase_timestamp"] <= str(end_date))
    ]

daily_orders_df = create_daily_orders_df(main_df)
category_sales = create_category_sales(main_df)
top_5_states_df = create_top_5_states_df(main_df)
rfm_df = create_rfm_df(main_df)

st.header('E-Commerce Dashboard :sparkles:')

st.subheader('Daily Orders')

col1 = st.columns(1)

with col1[0]:  # Access the first (and only) column in the tuple
    total_revenue = format_currency(daily_orders_df.revenue.sum(), "USD", locale='en_US')
    st.metric("Total Revenue", value=total_revenue)

fig, ax = plt.subplots(figsize=(16, 8))
ax.plot(
    daily_orders_df["order_purchase_timestamp"],
    daily_orders_df["order_count"],
    marker='o',
    linewidth=2,
    color="#08519c"
)
ax.tick_params(axis='y', labelsize=20)
ax.tick_params(axis='x', labelsize=15)

# Set the title for the plot
ax.set_title('Daily Orders Count', fontsize=18)

st.pyplot(fig)

st.subheader("Customer Demographics")

# List of colors to be used in the plot
colors = ['#00286b', '#0d54a0', '#547fd0', '#88adfd', '#c1e3ff']

# Creating a figure with dimensions 10x6 inches
plt.figure(figsize=(10, 6))

# Creating a bar plot using seaborn
sns.barplot(
    x="customer_state",
    y="customer_id",
    data=top_5_states_df,
    palette=colors
)

# Font settings for the plot title
font = {'weight': 'normal',
        'size': 13,
        }

# Adding a title to the plot
plt.title("Top 5 States by Customer Count", fontsize=15, fontdict=font)

# Adding labels to the x and y axes
plt.xlabel("State", fontdict=font)
plt.ylabel("Number of Customers", fontdict=font)

# Adjusting the plot layout for neatness
plt.tight_layout()

st.pyplot(plt)

st.subheader("Best & Worst Performing Product")

# Create subplots
fig, ax = plt.subplots(nrows=1, ncols=2, figsize=(24, 6))

# Define colors
colors = ['#00286b', '#c1e3ff', '#c1e3ff', '#c1e3ff', '#c1e3ff']

# Font settings for the plot title
font1 = {'weight': 'normal',
        'size': 15,
        }

font2 = {'weight': 'normal',
        'size': 15,
        }

# Plot the best performing products
sns.barplot(x='order_item_id', y='product_category_name', data=category_sales.head(5), palette=colors, ax=ax[0])
ax[0].set_ylabel(None)
ax[0].set_xlabel(None)
ax[0].set_title("Top 5 Best Selling Product Categories", loc="center", fontsize=15, fontdict=font1)
ax[0].tick_params(axis ='y', labelsize=12)

# Plot the worst performing products
sns.barplot(x='order_item_id', y='product_category_name', data=category_sales.sort_values(by="order_item_id", ascending=True).head(5), palette=colors, ax=ax[1])
ax[1].set_ylabel(None)
ax[1].set_xlabel(None)
ax[1].invert_xaxis()
ax[1].yaxis.set_label_position("right")
ax[1].yaxis.tick_right()
ax[1].set_title("Top 5 Least Selling Product Categories", loc="center", fontsize=15, fontdict=font2)
ax[1].tick_params(axis='y', labelsize=12)

# Display the plot
st.pyplot(fig)

st.subheader("Best Customer Based on RFM Parameters")

col1, col2, col3 = st.columns(3)

with col1:
    avg_recency = round(rfm_df.recency.mean(), 1)
    st.metric("Average Recency (days)", value=avg_recency)

with col2:
    avg_frequency = round(rfm_df.frequency.mean(), 2)
    st.metric("Average Frequency", value=avg_frequency)

with col3:
    avg_frequency = format_currency(rfm_df.monetary.mean(), "USD", locale='en_US')
    st.metric("Average Monetary", value=avg_frequency)

fig, ax = plt.subplots(nrows=1, ncols=3, figsize=(35, 15))

colors = ["#08519c"]

recency_data = rfm_df.sort_values(by="recency", ascending=True).head(5)
sns.barplot(y="recency", x="customer_id", data=recency_data, palette=colors, ax=ax[0])
ax[0].set_ylabel("Recency (days)", fontsize=14)
ax[0].set_xlabel("Customer ID", fontsize=14)
ax[0].set_title("Top Customers by Recency", loc="center", fontsize=18)
ax[0].tick_params(axis='x', labelrotation=90, labelsize=12)

frequency_data = rfm_df.sort_values(by="frequency", ascending=False).head(5)
sns.barplot(y="frequency", x="customer_id", data=frequency_data, palette=colors, ax=ax[1])
ax[1].set_ylabel("Frequency", fontsize=14)
ax[1].set_xlabel("Customer ID", fontsize=14)
ax[1].set_title("Top Customers by Frequency", loc="center", fontsize=18)
ax[1].tick_params(axis='x', labelrotation=90, labelsize=12)

monetary_data = rfm_df.sort_values(by="monetary", ascending=False).head(5)
sns.barplot(y="monetary", x="customer_id", data=monetary_data, palette=colors, ax=ax[2])
ax[2].set_ylabel("Monetary", fontsize=14)
ax[2].set_xlabel("Customer ID", fontsize=14)
ax[2].set_title("Top Customers by Monetary", loc="center", fontsize=18)
ax[2].tick_params(axis='x', labelrotation=90, labelsize=12)

st.pyplot(fig)

st.caption('Copyright (c) Dwiky Yudha Prasetya 2023')
