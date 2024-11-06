import pandas as pd
from bokeh.plotting import curdoc, figure
from bokeh.models import ColumnDataSource, Div
from bokeh.layouts import column, row
from bokeh.transform import dodge

# Load data
df = pd.read_csv("Perception_AI_Healthcare_2022_2024_with_counts.csv")

# Separate data by group
with_chatgpt_df = df[df["Group"] == "With ChatGPT Use"]
no_chatgpt_df = df[df["Group"] == "No ChatGPT Use"]

# Create ColumnDataSources for each group
with_chatgpt_counts_source = ColumnDataSource(with_chatgpt_df)
with_chatgpt_percentages_source = ColumnDataSource(with_chatgpt_df)
no_chatgpt_counts_source = ColumnDataSource(no_chatgpt_df)
no_chatgpt_percentages_source = ColumnDataSource(no_chatgpt_df)

# Define x-axis categories
categories = with_chatgpt_df["2022 Perception"]

# Create 2022 Perception Counts Bar Chart for "With ChatGPT Use"
p_counts_with = figure(x_range=categories, height=300, title="2022 Perception Counts (With ChatGPT Use)",
                       toolbar_location=None, tools="")
p_counts_with.vbar(x='2022 Perception', top='2022 Count', width=0.4, source=with_chatgpt_counts_source, color="navy")
p_counts_with.yaxis.axis_label = "Counts"

# Create 2024 Perception Percentages Bar Chart for "With ChatGPT Use"
p_percentages_with = figure(x_range=categories, height=300, title="2024 Perception Percentages (With ChatGPT Use)",
                            toolbar_location=None, tools="")
p_percentages_with.vbar(x=dodge('2022 Perception', -0.3, range=p_percentages_with.x_range), top="2024 - Don't know (%)", 
                        width=0.2, source=with_chatgpt_percentages_source, color="blue", legend_label="Don't know")
p_percentages_with.vbar(x=dodge('2022 Perception', -0.1, range=p_percentages_with.x_range), top="2024 - Benefits (%)", 
                        width=0.2, source=with_chatgpt_percentages_source, color="green", legend_label="Benefits")
p_percentages_with.vbar(x=dodge('2022 Perception', 0.1, range=p_percentages_with.x_range), top="2024 - Equal (%)", 
                        width=0.2, source=with_chatgpt_percentages_source, color="orange", legend_label="Equal")
p_percentages_with.vbar(x=dodge('2022 Perception', 0.3, range=p_percentages_with.x_range), top="2024 - Risks (%)", 
                        width=0.2, source=with_chatgpt_percentages_source, color="red", legend_label="Risks")
p_percentages_with.yaxis.axis_label = "Percentage"
p_percentages_with.legend.title = "2024 Perceptions"

# Create 2022 Perception Counts Bar Chart for "No ChatGPT Use"
p_counts_no = figure(x_range=categories, height=300, title="2022 Perception Counts (No ChatGPT Use)",
                     toolbar_location=None, tools="")
p_counts_no.vbar(x='2022 Perception', top='2022 Count', width=0.4, source=no_chatgpt_counts_source, color="navy")
p_counts_no.yaxis.axis_label = "Counts"

# Create 2024 Perception Percentages Bar Chart for "No ChatGPT Use"
p_percentages_no = figure(x_range=categories, height=300, title="2024 Perception Percentages (No ChatGPT Use)",
                          toolbar_location=None, tools="")
p_percentages_no.vbar(x=dodge('2022 Perception', -0.3, range=p_percentages_no.x_range), top="2024 - Don't know (%)", 
                      width=0.2, source=no_chatgpt_percentages_source, color="blue", legend_label="Don't know")
p_percentages_no.vbar(x=dodge('2022 Perception', -0.1, range=p_percentages_no.x_range), top="2024 - Benefits (%)", 
                      width=0.2, source=no_chatgpt_percentages_source, color="green", legend_label="Benefits")
p_percentages_no.vbar(x=dodge('2022 Perception', 0.1, range=p_percentages_no.x_range), top="2024 - Equal (%)", 
                      width=0.2, source=no_chatgpt_percentages_source, color="orange", legend_label="Equal")
p_percentages_no.vbar(x=dodge('2022 Perception', 0.3, range=p_percentages_no.x_range), top="2024 - Risks (%)", 
                      width=0.2, source=no_chatgpt_percentages_source, color="red", legend_label="Risks")
p_percentages_no.yaxis.axis_label = "Percentage"
p_percentages_no.legend.title = "2024 Perceptions"

# Layout in a 2x2 grid
layout = column(row(p_counts_with, p_counts_no), row(p_percentages_with, p_percentages_no))
curdoc().add_root(layout)
