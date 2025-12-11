'''
Name: Group 4 – Kevin Tom, Randy Estrin, Jinhua Yan
Data: 1. cocktails_categorized_detailed.csv (cocktail details scraped from Wikipedia),
2. cocktail_popularity.csv (simulated visitor counts by drink and year, from Kaggle),
plus live bar-location results from the Google Places API.
URL: [Link to your Streamlit Cloud app, if deployed]
Description: This script uses Streamlit to allow users to browse cocktails by alcohol base or mixing ingredients,
view images and recipe details, and visualize category counts using Altair charts.
It also includes a popular drinks explorer with a year slider and a list of the top ten most popular drinks.
Users can also search for nearby bars that serve the selected cocktail,
and view bar ratings and location information on an interactive Pydeck map
'''
import streamlit as st
import pandas as pd
import altair as alt
import requests
from streamlit import dataframe

# @st.cache_data speeds up apps by caching results of expensive data functions (like CSV/API loads),
# preventing re-computation on reruns. It returns a fresh copy each call, unlike st.cache_resource
# (for non-data objects).
@st.cache_data

# Define function to read the detailed cocktail dataset from CSV
def load_data():
    df = pd.read_csv("cocktails_categorized_detailed.csv")
    return df

# Assign dataset to variable by calling the load_data() function
df = load_data()

# Define which categories are mixers
mixer_categories = ["Carrot juice", "Pineapple juice", "Lemonade", "Lemon-lime soda",
    "Apple juice", "Grape juice", "Orange juice", "Ginger soda",
    "Cola", "Tonic"]

# Split dataset into alcohol-based cocktails vs mixer-based cocktails
alcohol_df = df[~df["category"].isin(mixer_categories)]
mixer_df = df[df["category"].isin(mixer_categories)]

# User chooses filter mode at the very start
# [ST4]
st.sidebar.header("Choose Filter Mode")
# [ST1]
filter_mode = st.sidebar.radio("Would you like to filter cocktails by:",("Alcohol Base", "Mixer"))

# Sidebar Filters (conditional based on mode)
# [DA4]
if filter_mode == "Alcohol Base":
    st.sidebar.header("Alcohol Filters")
    # [ST2]
    selected_category = st.sidebar.selectbox("Select a base spirit", alcohol_df["category"].unique())
    selected_cocktail = st.sidebar.selectbox(
        "Select a cocktail", alcohol_df[alcohol_df["category"] == selected_category]["name"].unique()
    )

    # Filtered DataFrame for alcohol mode
    # [DA5]
    filtered_df = alcohol_df[(alcohol_df["category"] == selected_category) & (alcohol_df["name"] == selected_cocktail)]
else:
    st.sidebar.header("Mixer Filters")
    selected_mixer = st.sidebar.selectbox("Select a mixer", mixer_df["category"].unique())
    selected_mixer_cocktail = st.sidebar.selectbox(
        "Select a cocktail (by mixer)", mixer_df[mixer_df["category"] == selected_mixer]["name"].unique()
)
    # Filtered DataFrame for mixer mode
    filtered_df = mixer_df[(mixer_df["category"] == selected_mixer) & (mixer_df["name"] == selected_mixer_cocktail)]

# App Layout
st.title("Cocktail Explorer")
st.write("Data sourced from Wikipedia’s List of Cocktails")

# Display Selected Cocktail (with images or default placeholder)
# Refer to section 6 of AI usage report
st.header(f"Selected Cocktail ({filter_mode})")
if not filtered_df.empty:
    row = filtered_df.iloc[0]
    st.subheader(row["name"])
    # Show cocktail image if available, otherwise show Wikimedia "No image available" placeholder
    if pd.notna(row["Image URL"]) and str(row["Image URL"]).strip() != "":
        st.image(row["Image URL"], width=300)
    else:
        st.image("https://upload.wikimedia.org/wikipedia/commons/a/ac/No_image_available.svg",width=300)
    # Show recipe link and details

    # This line uses Streamlit's st.markdown to render a clickable hyperlink
    st.markdown(f"[View recipe and ingredients on Wikipedia]({row['url']})")
    # For each of the following streamlit components, the if else logic will write the corresponding value if
    # available, else it writes "N/A"
    if pd.notna(row["Type"]) and str(row["Type"]).strip() != "":
        st.write("**Type:**", row["Type"])
    else:
        st.write("**Type:**", "N/A")
    if pd.notna(row["Base spirit"]) and str(row["Base spirit"]).strip() != "":
        st.write("**Base spirit:**", row["Base spirit"])
    else:
        st.write("**Base spirit:**", "N/A")
    if pd.notna(row["Ingredients"]) and str(row["Ingredients"]).strip() != "":
        st.write("**Ingredients:**", row["Ingredients"])
    else:
        st.write("**Ingredients:**", "N/A")
    if pd.notna(row["Preparation"]) and str(row["Preparation"]).strip() != "":
        st.write("**Preparation:**", row["Preparation"])
    else:
        st.write("**Preparation:**", "N/A")
    if pd.notna(row["Served"]) and str(row["Served"]).strip() != "":
        st.write("**Served:**", row["Served"])
    else:
        st.write("**Served:**", "N/A")
    if pd.notna(row["Standard drinkware"]) and str(row["Standard drinkware"]).strip() != "":
        st.write("**Glassware:**", row["Standard drinkware"])
    else:
        st.write("**Glassware:**", "N/A")
    if pd.notna(row["Standard garnish"]) and str(row["Standard garnish"]).strip() != "":
        st.write("**Garnish:**", row["Standard garnish"])
    else:
        st.write("**Garnish:**", "N/A")
else:
    st.info("No cocktail selected.")

# Visualization of cocktails_categorized_detailed.csv: Count of cocktails by alcohol category
# Only show this chart if user is filtering by Alcohol Base
if filter_mode == "Alcohol Base":
    category_counts = alcohol_df["category"].value_counts().reset_index()
    category_counts.columns = ["category", "count"]
    bar_chart = alt.Chart(category_counts).mark_bar().encode(
        x="category",
        y="count",
        tooltip=["category", "count"]
    ).properties(title="Number of Cocktails by Base Spirit")

    st.header("Cocktail Counts by Alcohol Category")
    # [VIZ2]
    # Refer to section 6 of AI usage report
    st.altair_chart(bar_chart, use_container_width=True)
# Load Popularity Dataset
@st.cache_data
def load_popularity_data():
    df_pop = pd.read_csv("cocktail_popularity.csv")
    return df_pop
popularity_df = load_popularity_data()
# Year Range Selection (above chart, not in sidebar)
st.header("Cocktail Popularity Explorer")
# [DA3]
min_year = int(popularity_df["year"].min())
max_year = int(popularity_df["year"].max())
# [ST3]
year_range = st.slider(
    "Select year range",
    min_value=min_year,
    max_value=max_year,
    value=(min_year, max_year),  # default full range
    step=1
)
start_year, end_year = year_range

# Filter Popularity Data ---
filtered_popularity = popularity_df[
    (popularity_df["year"] >= start_year) & (popularity_df["year"] <= end_year)
]
# Aggregate Visitors by Drink
drink_counts = (
    filtered_popularity.groupby("name")["visitors"]
    .sum()
    .reset_index()
    .sort_values("visitors", ascending=False)
)
# Select Top 10 Drinks
top10 = drink_counts.head(10)
# Altair Bar Chart
# refer to section 6 of AI usage report
popularity_chart = (
    alt.Chart(top10)
    .mark_bar()
    .encode(
        x=alt.X("name:N", sort="-y", title="Cocktail"),
        y=alt.Y("visitors:Q", title="Total Visitors"),
        tooltip=["name", "visitors"]
    )
    .properties(title=f"Top 10 Cocktails ({start_year}–{end_year})")
)
# Display Chart and Data
st.write(f"Showing top 10 cocktails between **{start_year}** and **{end_year}**")
# [VIZ1]
# refer to section 6 of AI usage report
st.altair_chart(popularity_chart, use_container_width=True)
st.dataframe(top10)
# Table of all cocktails
st.header("All Cocktails")
st.dataframe(df)

import requests
import pandas as pd
import streamlit as st

# Google Places API Key
# refer to section of AI usage report
API_KEY = "AIzaSyCYjUhQ_qM4wcZ4mRKf2GOl1sSgE1XAlbs"  # replace with your valid key
# Function to search bars for a cocktail in a city
def search_bars_for_cocktail(cocktail, city, max_results=20):
    url = (
        "https://maps.googleapis.com/maps/api/place/textsearch/json?"
        f"query={cocktail}+cocktail+bar+in+{city}&key={API_KEY}"
    )
    response = requests.get(url)
    data = response.json()
    results = data.get("results", [])
    # Limit the number of results returned using max_results
    df = pd.json_normalize(results)[:max_results]
    return df
# Streamlit UI
st.header("Find Bars Serving Your Cocktail")
cocktail = st.text_input("Enter a cocktail name")
city = st.text_input("Enter a city")
import pydeck as pdk
if st.button("Search"):
    df = search_bars_for_cocktail(cocktail, city)
    # refer to section 5 of AI usage report
    df_small = search_bars_for_cocktail(cocktail, city, 30)
    if df_small.empty:
        st.info("No results found.")
    else:
        # Sort by rating (descending) and take top 10
        # [DA2]
        df_top5 = df_small.sort_values(["rating", "user_ratings_total"], ascending=[False, False]).head(5)

        # Set the index to the bar name
        df_top5 = df_top5.set_index("name")
    if df.empty:
        st.info("No results found.")
    else:
        # Sort by rating (descending) and take top 10
        # [DA2]
        df_top10 = df.sort_values(["rating", "user_ratings_total"], ascending=[False, False]).head(10)
        # Set the index to the bar name
        df_top10 = df_top10.set_index("name")
        # Rename columns to match Pydeck expectations
        df_top10 = df_top10.rename(columns={"geometry.location.lat": "lat","geometry.location.lng": "lon"})
        # Collect lat/lon pairs
        # [PY4 and DA8]
        # refer to section 3 of AI usage report
        coords = [(row["lat"], row["lon"]) for _, row in df_top10.iterrows()]
        # Define Pydeck layer with tooltips
        # refer to section 4 of AI usage report
        layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_top10.reset_index(),  # keep 'name' available for tooltip
            get_position='[lon, lat]',
            get_color=[200, 30, 0, 160],  # red dots
            get_radius=100,
            pickable=True
)
        # Tooltip shows name, address, rating, and number of ratings
        tooltip = {"text": "{name}\n{formatted_address}\nRating: {rating} ({user_ratings_total} reviews)"}
        # Set the map view using the list comprehension results
        # refer to section 4 of AI usage report
        view_state = pdk.ViewState(
            latitude=sum(lat for lat, _ in coords) / len(coords),
            longitude=sum(lon for _, lon in coords) / len(coords),
            zoom=11
        )
        # Render the map with tooltips
        # [VIZ4 MAP]
        # refer to section 4 of AI usage report
        st.pydeck_chart(pdk.Deck(layers=[layer], initial_view_state=view_state, tooltip=tooltip))
        # Show details table with bar names as index
        #[VIZ3]
        st.write("### Top 10 Bars")
        st.write(df_top10[["rating","user_ratings_total","formatted_address","lat","lon"]])
        #Added section to display second call results
        st.write("### Top 5 Bars")
        st.write(df_top5[["rating","user_ratings_total","formatted_address"]])