from pathlib import Path
import pandas as pd
import streamlit as st
from typing import List, Tuple
import plotly.express as px
import pendulum

def set_page_config():
    st.set_page_config(
        page_title="Sales Dashboard",
        page_icon=":bar_chart:",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    st.markdown("<style> footer {visibility: hidden;} </style>", unsafe_allow_html=True)

# Use the raw URL for direct access to the file content
INPUT_DATA_URI = "https://raw.githubusercontent.com/MouslyDiaw/creez-dashboard/main/data"

# home directory
HOME_DIR = Path.cwd()
DATA_DIR = Path(HOME_DIR, "data")
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Load impressions data
df_impressions = pd.read_csv(
    f"{INPUT_DATA_URI}/impressions.csv",
    sep=",",
    on_bad_lines='skip',
    dtype={
        "cookie_id": str,
        "campaign_id": str,
        "external_site_id": str,
    }
)

# Convert timestamp to date and create a new column named 'date_impression'
df_impressions['date_impression'] = pd.to_datetime(df_impressions['timestamp'], unit='s')
###clis
df_clics = pd.read_csv(f"{INPUT_DATA_URI}/clics.csv",
                       sep=",", on_bad_lines='skip',
                       dtype={"cookie_id": str}
                      )
# convert timestamp to date and create new column named 'date'
df_clics['date_clic'] = pd.to_datetime(df_clics['timestamp'], unit='s')

#######achat######################
df_achats = pd.read_csv(f"{INPUT_DATA_URI}/achats.csv",
                             sep=",", on_bad_lines='skip',
                        dtype={"cookie_id": str,
                              "product_id": str,
                              }
                       )
# convert timestamp to date and create new column named 'date'
df_achats['date_achat'] = pd.to_datetime(df_achats['timestamp'], unit='s')
#########Merge Data#######################
data = (df_impressions
        # add clic on impressions that have this action
        .merge(df_clics.drop("timestamp", axis=1), how="left", on="cookie_id")
        # add clic on impressions that have this action
        .merge(df_achats.drop("timestamp", axis=1), how="left", on="cookie_id")
        .assign(is_clic=lambda dfr: dfr.date_clic.notnull(),
                is_achat=lambda dfr: dfr.date_achat.notnull(),
               )
       )


# Uncomment and complete the necessary parts of the code below
@st.cache_data
def load_data() -> pd.DataFrame:

    return data

# Define other functions as needed for your dashboard
######FILTER


def filter_data(data: pd.DataFrame, column: str, values: List[str]) -> pd.DataFrame:
    return data[data[column].isin(values)] if values else data

######KPI############
@st.cache_data
def calculate_kpis(data: pd.DataFrame) -> List[float]:
    nb_impressions = len(data)
    nb_clics, nb_achats = data[["is_clic", "is_achat"]].sum()


    return [nb_impressions, nb_clics, nb_achats]

########
def display_kpi_metrics(kpis: List[float], kpi_names: List[str]):
    st.header("KPI Metrics")
    for i, (col, (kpi_name, kpi_value)) in enumerate(zip(st.columns(4), zip(kpi_names, kpis))):
        col.metric(label=kpi_name, value=kpi_value,
                  )



#################





#################Slide bar #################
def display_sidebar(data: pd.DataFrame) -> Tuple[List[str], List[str], List[str]]:
    st.sidebar.header("Filters")
    # start_date = pd.Timestamp(st.sidebar.date_input("Start date", data['date_impression'].min().date()))
    # end_date = pd.Timestamp(st.sidebar.date_input("End date", data['date_impression'].max().date()))

    ages_lines = sorted(data['age'].unique())
    selected_ages_lines = st.sidebar.multiselect("Select age", ages_lines, ages_lines)

    selected_campaign = st.sidebar.multiselect("Select Campaign", data['campaign_id'].unique())


    return selected_ages_lines, selected_campaign


#############CHARTS
def display_charts(data: pd.DataFrame):


    # if combine_product_lines:
    #     fig = px.area(data, x='ORDERDATE', y='SALES',
    #                   title="Sales by Product Line Over Time", width=900, height=500)
    # else:
    #     fig = px.area(data, x='ORDERDATE', y='SALES', color='PRODUCTLINE',
    #                   title="Sales by Product Line Over Time", width=900, height=500)
    #
    # fig.update_layout(margin=dict(l=20, r=20, t=50, b=20))
    # fig.update_xaxes(rangemode='tozero', showgrid=False)
    # fig.update_yaxes(rangemode='tozero', showgrid=True)
    # st.plotly_chart(fig, use_container_width=True)



    st.subheader("CA by Campaign")
    ca_per_campaign = data.groupby("campaign_id", as_index=False).agg(ca=("price", "sum"))
    ca_per_campaign["campaign_id"] = ca_per_campaign["campaign_id"].astype(str)
    fig = px.bar(data_frame=ca_per_campaign, x="campaign_id", y="ca",
                 text_auto=True,
                 title="CA per campaign",
                 width=500,
                 height=400,
                 )

    # Affichage du graphique à barres corrigé
    st.plotly_chart(fig)
    st.subheader("Number of clics")
    nb_clics_per_hour = (data
                         .groupby(["campaign_id", pd.Grouper(key="date_clic", freq="D")])
                         .agg(nb_clics=("is_clic", "sum"))
                         .reset_index(drop=False)
                         )
    fig2 = px.line(data_frame=(nb_clics_per_hour
                              .groupby("date_clic", as_index=False)
                              .agg(nb_total_clics=("nb_clics", "sum"))
                              ),
                  x='date_clic', y="nb_total_clics",
                  title="#Clics by day")
    st.plotly_chart(fig2)
    st.subheader("best_products")
    best_products = (data
                     .groupby("product_id", as_index=False, dropna=True)
                     .agg(nb_achats=("is_achat", "sum"),
                          )
                     .nlargest(10, columns=["nb_achats"])
                     )
    fig3 = px.pie(data_frame=best_products, names="product_id", values="nb_achats",
                 hole=.3, width=400,
                 )
    st.plotly_chart(fig3)








def main():
    set_page_config()
    data = load_data()
    selected_ages_lines, selected_campaign = display_sidebar(data)
    st.title("📊 Sales Dashboard")
    filtered_data = data.copy()

    filtered_data = filter_data(filtered_data, 'campaign_id', selected_campaign)
    filtered_data = filter_data(filtered_data, 'age', selected_ages_lines)

    kpis = calculate_kpis(filtered_data)
    kpi_names = ["Total des impressions", "Total clics", "Total achat"]
    display_kpi_metrics(kpis, kpi_names)

    display_charts(filtered_data)

    # Uncomment and complete the necessary parts of the code below
    # selected_product_lines, selected_countries, selected_statuses = display_sidebar(data)

    # filtered_data = data.copy()
    # filtered_data = filter_data(filtered_data, 'PRODUCTLINE', selected_product_lines)
    # filtered_data = filter_data(filtered_data, 'COUNTRY', selected_countries)
    # filtered_data = filter_data(filtered_data, 'STATUS', selected_statuses)

    # kpis = calculate_kpis(filtered_data)
    # kpi_names = ["Total Sales", "Total Orders", "Average Sales per Order", "Unique Customers"]
    # display_kpi_metrics(kpis, kpi_names)

    # display_charts(filtered_data)

if __name__ == '__main__':
    main()
