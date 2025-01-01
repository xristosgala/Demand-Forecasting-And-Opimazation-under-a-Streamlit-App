import streamlit as st
import pandas as pd
from io import StringIO
import io
import plotly.express as px
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_squared_error, r2_score, mean_absolute_error
import matplotlib.pyplot as plt
from sklearn.tree import DecisionTreeClassifier
from sklearn import tree
import xgboost as xgb
from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
import numpy as np
import tensorflow as tf
from tensorflow import keras
from keras.layers import Input, LSTM, Dense
from keras.models import Sequential
from statsmodels.tsa.ar_model import AutoReg
from statsmodels.tsa.stattools import acf, pacf
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from sklearn.ensemble import StackingRegressor
from xgboost import XGBRegressor
from sklearn.preprocessing import StandardScaler, QuantileTransformer
import seaborn as sns
import plotly.express as px
import category_encoders as ce
import math
from matplotlib.offsetbox import AnchoredText
from sklearn.model_selection import TimeSeriesSplit, GridSearchCV
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.preprocessing import OneHotEncoder
from pulp import LpProblem, LpMinimize, LpVariable, lpSum, LpStatus
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

# Function to capture the output of .info() into a string
def get_dataframe_info(df):
    buffer = StringIO()
    df.info(buf=buffer)
    return buffer.getvalue()

st.title("Food Demand Prediction and Optimization App")
st.header("1. Upload Your Datasets")

# Upload the three CSV files
train_data_file = st.file_uploader("Choose the Train Data CSV file", type=["csv"])
fulfilment_center_data_file = st.file_uploader("Choose the Fulfilment Center Data CSV file", type=["csv"])
meal_data_file = st.file_uploader("Choose the Meal Data CSV file", type=["csv"])

# Check if all three files are uploaded
if train_data_file is not None and fulfilment_center_data_file is not None and meal_data_file is not None:
    # Load the datasets
    train_data = pd.read_csv(train_data_file)
    fulfilment_center_data = pd.read_csv(fulfilment_center_data_file)
    meal_data = pd.read_csv(meal_data_file)

    merged_df = pd.merge(train_data, fulfilment_center_data, on='center_id')
    final_merged_df = pd.merge(merged_df, meal_data, on='meal_id')

    st.success("All files uploaded successfully!")

    st.info("For better understanding all datasets were merged into one")

    # Separate Section: Total Demand Time Series
    st.header("2. Exploratory Data Analysis (EDA)")

    st.subheader("Descriptive Statistics")

    # Create a list of options for the user to select
    eda_options_descriptive = st.multiselect(
        "Please, select any of the following descriptive processes to perform",
        ["Preview of the dataset", "Show statistics of the dataset", "Show any missing values of the dataset", "Show dataset information"]
    )

    # Perform actions based on the selected EDA option
    if "Preview of the dataset" in eda_options_descriptive:
        st.subheader("Merged Dataset Preview")
        st.dataframe(final_merged_df.head())

    if "Show statistics of the dataset" in eda_options_descriptive:
        st.subheader("Merged Dataset Statistics")
        st.write(final_merged_df.describe())

    if "Show any missing values of the dataset" in eda_options_descriptive:
        st.subheader("Merged Dataset Missing Values")
        st.write(final_merged_df.isna().sum())

    if "Show dataset information" in eda_options_descriptive:
        st.subheader("Merged Dataset Information")
        buffer = io.StringIO()
        final_merged_df.info(buf=buffer)
        info_str = buffer.getvalue()
        st.text(info_str)

    st.subheader("Data Visualization")

    # Create a list of options for the user to select
    eda_options_plot = st.multiselect(
        "Please, select any of the following visualization to generate",
        ["Show the total number of orders time series", "Select a center id and a meal id to generate a line plot"]
    )

    if "Show the total number of orders time series" in eda_options_plot:
        st.subheader("Total Weekly Number of Orders")

        # Group the data to create a time series
        df_plot = final_merged_df.groupby(['week'])['num_orders'].sum().reset_index()

        # Create the interactive Plotly line chart
        fig = px.line(
            df_plot,
            x='week',
            y='num_orders',
            markers=True,
            labels={'week': 'Week', 'num_orders': 'Number of Orders'}
        )

        # Display the plot
        st.plotly_chart(fig, use_container_width=True)

          # Add a new EDA option for selecting center and meal
    if "Select a center id and a meal id to generate a line plot" in eda_options_plot:

        # Allow the user to select a center
        centers = final_merged_df['center_id'].unique()  # Unique center IDs
        selected_center = st.selectbox("Select a Center ID", centers)

        # Filter the data based on the selected center to get available meals
        filtered_data_center = final_merged_df[final_merged_df['center_id'] == selected_center]
        meals = filtered_data_center['meal_id'].unique()  # Unique meal IDs for the selected center
        selected_meal = st.selectbox("Select a Meal ID", meals)

        # Display the selected center and meal in the subheader
        st.subheader(f"Weekly Number of Orders for Center {selected_center} and Meal {selected_meal}")

        # Filter the dataset for the selected center and meal
        df_plot_2 = final_merged_df[
            (final_merged_df['center_id'] == selected_center) &
            (final_merged_df['meal_id'] == selected_meal)
        ]

        # Create the interactive plot
        fig = px.line(
            df_plot_2,
            x='week',
            y='num_orders',
            markers=True,
            labels={'week': 'Week', 'num_orders': 'Number of Orders'}
        )

        # Display the plot
        st.plotly_chart(fig)


    st.subheader("Explore Relationships Between Variables")

    # Create a list of options for the user to select
    eda_options_relationships = st.multiselect(
        "Please, select any of the following visualizations to discover relationships between features:",
        ["Create histograms and boxplots", "Generate correlation heatmaps and a pair plot"]
    )

    # Define numerical features
    numerical_features = ['checkout_price', 'base_price', 'num_orders']

    if "Create histograms and boxplots" in eda_options_relationships:
        st.subheader("Histogram and Boxplot of the Numerical Features")

        # Create subplots for histograms and box plots
        fig, axes = plt.subplots(2, len(numerical_features), figsize=(15, 8))

        for i, feature in enumerate(numerical_features):
            # Histogram
            sns.histplot(final_merged_df[feature], kde=True, ax=axes[0, i])
            axes[0, i].set_title(f'Histogram of {feature}')

            # Boxplot
            sns.boxplot(y=final_merged_df[feature], ax=axes[1, i])
            axes[1, i].set_title(f'Boxplot of {feature}')

        plt.tight_layout()  # Adjust spacing
        st.pyplot(fig)

    if "Generate correlation heatmaps and a pair plot" in eda_options_relationships:
        st.subheader("Correlation Heatmap and Pair Plot")

        # Correlation matrices
        pearson_corr = final_merged_df[numerical_features].corr(method='pearson')
        spearman_corr = final_merged_df[numerical_features].corr(method='spearman')

        # Create subplots for correlation heatmaps
        fig, axes = plt.subplots(1, 2, figsize=(12, 6))

        # Pearson correlation heatmap
        sns.heatmap(pearson_corr, annot=True, cmap='coolwarm', fmt=".2f", ax=axes[0])
        axes[0].set_title("Pearson Correlation Matrix")

        # Spearman correlation heatmap
        sns.heatmap(spearman_corr, annot=True, cmap='coolwarm', fmt=".2f", ax=axes[1])
        axes[1].set_title("Spearman Correlation Matrix")

        plt.tight_layout()
        st.pyplot(fig)

        # Pair plot
        st.write("Pair Plot of Numerical Features")
        pairplot_fig = sns.pairplot(final_merged_df[numerical_features], diag_kind='hist', markers="o", height=2.5)
        st.pyplot(pairplot_fig.fig)



    st.header("3. Run XGboost model to predict the number of orders for the last 10 days")

    # Ask the user if they want to run the model
    run_model = st.radio("Do you want to run the XGBoost model?", ("No", "Yes"))

    if run_model == "Yes":
        st.subheader("Model Results")

        # Data preparation
        df_additional_features = final_merged_df.copy()
        df_additional_features['NewCategoryCenter'] = df_additional_features['category'] + '_' + df_additional_features['center_type'].astype(str)
        df_additional_features['NewCuisineCenter'] = df_additional_features['cuisine'] + '_' + df_additional_features['center_type'].astype(str)

        train_df = df_additional_features[df_additional_features["week"] < 136]
        test_df = df_additional_features[df_additional_features["week"] >= 136]
        train_df = train_df.copy()
        test_df = test_df.copy()
        train_df.drop(columns=['id'], inplace=True)
        test_df.drop(columns=['id'], inplace=True)

        categorical_features = ['center_id', 'meal_id', 'city_code', 'region_code', 'center_type',
                                'category', 'cuisine', 'op_area', 'NewCategoryCenter', 'NewCuisineCenter']

        one_hot_encoder = OneHotEncoder(sparse_output=False, handle_unknown='ignore')
        one_hot_encoder.fit(train_df[categorical_features])

        train_encoded = one_hot_encoder.transform(train_df[categorical_features])
        test_encoded = one_hot_encoder.transform(test_df[categorical_features])

        train_encoded_df = pd.DataFrame(train_encoded, columns=one_hot_encoder.get_feature_names_out(categorical_features), index=train_df.index)
        test_encoded_df = pd.DataFrame(test_encoded, columns=one_hot_encoder.get_feature_names_out(categorical_features), index=test_df.index)

        train_df_encoded = pd.concat([train_df.drop(columns=categorical_features), train_encoded_df], axis=1)
        test_df_encoded = pd.concat([test_df.drop(columns=categorical_features), test_encoded_df], axis=1)

        X_train, y_train = train_df_encoded.drop(columns=['num_orders']), train_df_encoded['num_orders']
        X_test, y_test = test_df_encoded.drop(columns=['num_orders']), test_df_encoded['num_orders']

        # Convert to DMatrix format
        dtrain = xgb.DMatrix(X_train, label=y_train)
        dtest = xgb.DMatrix(X_test, label=y_test)

        # XGBoost model training
        xgb_params = {
            'objective': 'reg:squarederror',
            'tree_method': 'hist',
            'eval_metric': 'rmse',
            'device': 'cpu',  # Adjust based on availability
            'learning_rate': 0.1,
            'max_depth': 7,
            'random_state': 42
        }
        xgb_regressor = xgb.train(xgb_params, dtrain, num_boost_round=200)

        # Predictions
        y_pred = xgb_regressor.predict(dtest)

        # Calculate metrics
        mse = mean_squared_error(y_test, y_pred)
        rmse = mse ** 0.5
        mae = mean_absolute_error(y_test, y_pred)
        mape = (abs((y_test - y_pred) / y_test).mean()) * 100
        r2 = r2_score(y_test, y_pred)

        # Create a DataFrame for metrics
        metrics_data = {
            "Metric": [
                "Mean Absolute Error (MAE)",
                "Mean Absolute Percentage Error (MAPE)",
                "Root Mean Squared Error (RMSE)",
                "R² Score"
            ],
            "Value": [
                f"{mae:.2f}",
                f"{mape:.2f}%",
                f"{rmse:.2f}",
                f"{r2:.2f}"
            ]
        }
        metrics_df = pd.DataFrame(metrics_data)

        # Display the results
        st.table(metrics_df)

    elif run_model == "No":
        st.write("You chose not to run the model.")

    # Add an option to ask the user if they want to run the optimization model
    st.header("4. Optimization Model")

    # Prompt the user
    run_optimization = st.radio("Do you want to run the optimization model?", ("No", "Yes"))

    if run_optimization == "Yes":
        if run_model != "Yes":
            st.error("You need to run the XGBoost model first to use the optimization model.")
        else:
            # Create a variable to store the test_df
            data = test_df.copy()

            # Convert the y_pred variable from numpy array to pandas Series
            y_pred_series = pd.Series(y_pred, index=data.index, name='predicted')

            # Concatenate the test data with actual and predicted values
            data = pd.concat([data, y_pred_series], axis=1)

            # Drop the actual 'num_orders' column and reorder the columns
            data.drop(['num_orders'], axis=1, inplace=True)
            data = data[['week', 'center_id', 'meal_id', 'checkout_price', 'predicted']]

            # Step 1: Display available center IDs
            centers = data['center_id'].unique()

            # Step 2: User selects centers
            selected_centers = st.multiselect("Select the center IDs to include:", centers)
            if not selected_centers:
                st.warning("Please select at least one center to proceed.")
            else:
                # Filter data for selected centers
                filtered_data_center = data[data['center_id'].isin(selected_centers)]

                # Step 3: Find common meals across selected centers
                center_meals = filtered_data_center.groupby('center_id')['meal_id'].unique()

                common_meals = set(center_meals.iloc[0])  # Start with meals from the first center
                for meals in center_meals[1:]:
                    common_meals &= set(meals)  # Keep only meals that are common to all centers

                # Convert the common meals back to a list for user selection
                common_meals = list(common_meals)

                # Step 4: User selects meals
                selected_meals = st.multiselect("Select the meal IDs to include:", common_meals)
                if not selected_meals:
                    st.warning("Please select at least one meal to proceed.")
                else:
                    # Function to check meal availability over 10 weeks
                    def is_meal_available_for_10_weeks(meal_id, center_id, data):
                        filtered_data = data[(data['meal_id'] == meal_id) &
                                            (data['center_id'] == center_id) &
                                            (data['week'] >= 136) &
                                            (data['week'] <= 145)]
                        return len(filtered_data['week'].unique()) >= 10

                    # Step 5: Validate meal availability
                    valid_meals = []
                    invalid_meals_details = []

                    for meal in selected_meals:
                        invalid_centers = [center for center in selected_centers if not is_meal_available_for_10_weeks(meal, center, filtered_data_center)]
                        if not invalid_centers:
                            valid_meals.append(meal)
                        else:
                            invalid_meals_details.append({'meal': meal, 'invalid_centers': invalid_centers})

                    # Display invalid meals and their centers
                    if invalid_meals_details:
                        st.error("Some selected meals do not contain last 10 weeks for predicting period.")
                        for detail in invalid_meals_details:
                            st.write(f"Meal: {detail['meal']} is not valid in centers: {detail['invalid_centers']}")
                    else:
                        st.success("All selected meals are valid in all centers.")

                    # Step 6: Ask user to proceed with valid meals
                    if valid_meals:
                        proceed = st.radio(f"Do you want to proceed with the valid meals {valid_meals}?", ["No", "Yes"])
                        if proceed == "Yes":
                            # Filter data for valid meals
                            filtered_data_meal = filtered_data_center[filtered_data_center['meal_id'].isin(valid_meals)]

                            selected_meals = valid_meals

                            # Collect ordering, holding, and unit costs for each meal
                            ordering_cost = {}
                            holding_cost = {}
                            unit_cost = {}

                            st.subheader("Enter Costs for Each Meal")

                            for meal_id in selected_meals:
                                st.markdown(f" #### Meal ID {meal_id}")
                                ordering_cost[meal_id] = st.number_input(f"Enter ordering cost for Meal {meal_id}:", min_value=0.0, step=0.01)
                                holding_cost[meal_id] = st.number_input(f"Enter holding cost per unit for Meal {meal_id}:", min_value=0.0, step=0.01)
                                unit_cost[meal_id] = st.number_input(f"Enter unit cost for Meal {meal_id}:", min_value=0.0, step=0.01)

                            # Create dictionaries for demand and checkout price, indexed by meal_id and week
                            demand = {}
                            checkout_price = {}

                            for center_id in selected_centers:
                                center_data = filtered_data_meal[filtered_data_meal['center_id'] == center_id]  # Filter data for the center

                                demand_temp = {}
                                checkout_price_temp = {}

                                for meal_id in selected_meals:
                                    meal_data = center_data[center_data['meal_id'] == meal_id]  # Filter data for the meal

                                    # Store predicted demand and checkout prices for each week
                                    demand_temp[meal_id] = meal_data['predicted'].tolist()
                                    checkout_price_temp[meal_id] = meal_data['checkout_price'].tolist()

                                demand[center_id] = demand_temp
                                checkout_price[center_id] = checkout_price_temp

                            weeks = list(range(1, len(filtered_data_meal['week'].unique().tolist()) + 1))  # List of weeks
                            meals = selected_meals
                            centers = selected_centers

                            # Define baseline budget using realistic weekly demand
                            baseline_budget = {}
                            margin = 1.2  # Additional margin to account for extra costs

                            for center in centers:
                                total_demand_cost = 0
                                for meal in meals:
                                    weekly_demand = demand[center][meal]  # Predicted demand per week
                                    for t, demand_value in enumerate(weekly_demand):
                                        total_demand_cost += unit_cost[meal] * demand_value
                                baseline_budget[center] = total_demand_cost / (len(weeks) - 1) * margin  # Adjusted with margin

                            # Display calculated baseline budgets
                            st.subheader("Baseline Budget Suggestion with 1.2 Margin")
                            for center, budget_value in baseline_budget.items():
                                st.write(f"Center {center}: {budget_value:.2f}")

                            # Collect user-defined budget and warehouse capacity for each center
                            budget = {}
                            warehouse_capacity = {}
                            initial_inventory = {}

                            st.subheader("Enter Budget and Warehouse Capacity")

                            for center_id in selected_centers:
                                st.markdown(f"#### Center ID {center_id}")
                                budget[center_id] = st.number_input(f"Enter the weekly budget for center {center_id}:", min_value=0.0, step=0.01)
                                warehouse_capacity[center_id] = st.number_input(f"Enter the warehouse capacity for center {center_id}:", min_value=0, step=1)

                                initial_inventory_temp = {}
                                for meal_id in selected_meals:
                                    initial_inventory_temp[meal_id] = st.number_input(
                                        f"Enter initial inventory for Meal {meal_id} in center {center_id}:", min_value=0, step=1
                                    )

                                initial_inventory[center_id] = initial_inventory_temp

                            # Define lead time
                            lead_time = 1

                            # Ensure `selected_meals`, `selected_centers`, `demand`, `checkout_price`, `unit_cost`, `ordering_cost`, `holding_cost`, `budget`, and `warehouse_capacity` are defined.

                            # Define the optimization problem

                            prob = LpProblem("Multiple_Centers_Meals_Optimization", LpMinimize)

                            # Decision variables
                            order_qty = LpVariable.dicts("Order", (centers, meals, weeks), lowBound=0, cat="Integer")
                            inventory = LpVariable.dicts("Inventory", (centers, meals, weeks), lowBound=0, cat="Integer")
                            order_indicator = LpVariable.dicts("OrderIndicator", (centers, meals, weeks), cat="Binary")
                            unmet_demand = LpVariable.dicts("UnmetDemand", (centers, meals, weeks), lowBound=0, cat="Integer")

                            # Objective function: Minimize ordering, holding, and penalty costs
                            prob += lpSum(
                                ordering_cost[meal] * order_indicator[center][meal][t] +
                                order_qty[center][meal][t] * unit_cost[meal] +
                                holding_cost[meal] * inventory[center][meal][t] +
                                checkout_price[center][meal][t-1] * unmet_demand[center][meal][t]
                                for center in centers for meal in meals for t in weeks
                            )

                            # Constraints
                            for center in centers:
                                for t in weeks:
                                    for meal in meals:
                                        # Inventory balance constraint
                                        if t == 1:
                                            prob += inventory[center][meal][t] == initial_inventory[center][meal] - demand[center][meal][t-1] + unmet_demand[center][meal][t]
                                        else:
                                            prob += inventory[center][meal][t] == inventory[center][meal][t-1] + order_qty[center][meal][t-lead_time] - demand[center][meal][t-1] + unmet_demand[center][meal][t] - unmet_demand[center][meal][t-1]

                                        # Link binary variable to order quantity using Big-M method
                                        prob += order_qty[center][meal][t] <= 1000000 * order_indicator[center][meal][t]

                                    # Weekly budget constraint
                                    prob += lpSum(order_qty[center][meal][t] * unit_cost[meal] + ordering_cost[meal] * order_indicator[center][meal][t] for meal in meals) <= budget[center]

                                    # Warehouse capacity constraint
                                    prob += lpSum(inventory[center][meal][t] for meal in meals) <= warehouse_capacity[center]

                            # Solve the problem
                            with st.spinner("Solving the problem..."):
                                prob.solve()

                            # Check solution status
                            solution_status = LpStatus[prob.status]
                            st.write(f"Solution Status: {solution_status}")

                            # Collect results
                            results = []
                            for center in centers:
                                for meal in meals:
                                    for t in weeks:
                                        results.append({
                                            "Center": center,
                                            "Week": t,
                                            "Meal": meal,
                                            "Order": order_qty[center][meal][t].varValue,
                                            "Inventory": inventory[center][meal][t].varValue,
                                            "Unmet Demand": unmet_demand[center][meal][t].varValue
                                        })

                            results_df = pd.DataFrame(results)
                            st.subheader("Optimization Results")
                            st.dataframe(results_df)

                            # Metrics Calculation
                            total_ordering_cost = 0
                            total_holding_cost = 0
                            total_penalty_cost = 0
                            total_unmet_demand = 0
                            unmet_demand_frequency = 0
                            budget_utilization = {}

                            for center in centers:
                                center_spending = 0  # Total spending for the center
                                for meal in meals:
                                    unmet_demand_value = unmet_demand[center][meal][len(weeks)].varValue
                                    total_unmet_demand += unmet_demand_value

                                    for t in weeks:
                                        order_cost = ordering_cost[meal] * order_indicator[center][meal][t].varValue + order_qty[center][meal][t].varValue * unit_cost[meal]
                                        holding_cost_week = holding_cost[meal] * inventory[center][meal][t].varValue
                                        penalty_cost_week = checkout_price[center][meal][t-1] * unmet_demand[center][meal][t].varValue

                                        total_ordering_cost += order_cost
                                        total_holding_cost += holding_cost_week
                                        total_penalty_cost += penalty_cost_week

                                        if unmet_demand[center][meal][t].varValue > 0:
                                            unmet_demand_frequency += 1

                                        center_spending += order_cost

                                budget_utilization[center] = round(center_spending / (budget[center] * (len(weeks) - 1)), 2)

                            evaluation_results = {
                                "Total Cost": total_ordering_cost + total_holding_cost + total_penalty_cost,
                                "Ordering Cost": total_ordering_cost,
                                "Holding Cost": total_holding_cost,
                                "Penalty Cost": total_penalty_cost,
                                "Total Unmet Demand": total_unmet_demand,
                                "Unmet Demand Frequency": unmet_demand_frequency,
                                "Budget Utilization": budget_utilization
                            }

                            evaluation_results = pd.DataFrame(evaluation_results)
                            st.subheader("Evaluation Metrics")
                            st.dataframe(evaluation_results)


                            st.subheader("Visualization Plot")
                            # Get unique centers and meals
                            unique_centers = results_df["Center"].unique()
                            unique_meals = results_df["Meal"].unique()

                            # Use a qualitative color palette for more distinct colors
                            color_palette = px.colors.qualitative.Plotly
                            num_colors = len(color_palette)
                            color_mapping = {meal: color_palette[i % num_colors] for i, meal in enumerate(unique_meals)}

                            # Create subplots: 1 column per center
                            num_rows = 1
                            num_cols = len(unique_centers)
                            fig = make_subplots(
                                rows=num_rows,
                                cols=num_cols,
                                subplot_titles=[f"Center {center}" for center in unique_centers],
                                shared_xaxes=True,
                            )

                            # Plot data for each center
                            for i, center in enumerate(unique_centers):
                                center_data = results_df[results_df["Center"] == center]
                                for meal in unique_meals:
                                    meal_data = center_data[center_data["Meal"] == meal]

                                    # Ensure legendgroup is a string
                                    legend_group = str(meal)

                                    # Add bars for unmet demand
                                    fig.add_trace(
                                        go.Bar(
                                            x=meal_data["Week"],
                                            y=meal_data["Unmet Demand"],
                                            name=f"Unmet Demand for {meal}",
                                            marker=dict(color=color_mapping[meal], opacity=0.6),
                                            legendgroup=legend_group,
                                            showlegend=(i == 0),  # Show legend only once per meal
                                        ),
                                        row=1,
                                        col=i + 1,
                                    )

                                    # Add lines for order quantities
                                    fig.add_trace(
                                        go.Scatter(
                                            x=meal_data["Week"],
                                            y=meal_data["Order"],
                                            mode="lines+markers",
                                            name=f"Order Quantity for {meal}",
                                            line=dict(width=2, color=color_mapping[meal]),
                                            legendgroup=legend_group,
                                            showlegend=(i == 0),  # Show legend only once per meal
                                        ),
                                        row=1,
                                        col=i + 1,
                                    )

                            # Update layout
                            fig.update_layout(
                                title="Order Quantities and Unmet Demand Over Time by Meal and Center",
                                xaxis_title="Weeks",
                                yaxis_title="Order Quantity And Unmet Demand",
                                height=600,
                                legend_title="Legend",
                                template="plotly"
                            )

                            # Display the figure in Streamlit
                            st.plotly_chart(fig, use_container_width=True)

                            st.subheader("Sensitivity Analysis")

                            # Ask user if they want to perform sensitivity analysis
                            proceed = st.radio(f"Do you want to perform a Sensitivity Analysis?", ["No", "Yes"])
                            if proceed == "Yes":
                                # Ask for budget reduction levels
                                reduction_input = st.text_input("Enter budget reduction percentage levels (comma-separated):", "10,20,30")

                                if reduction_input:
                                    try:
                                        # Parse the reduction levels
                                        budget_reduction_levels = [float(budget.strip()) for budget in reduction_input.split(",")]

                                        # Store results for sensitivity analysis
                                        sensitivity_results = []

                                        # Loop over budget reduction levels
                                        for reduction in budget_reduction_levels:
                                            # Adjust budget
                                            adjusted_budget = {center: budget[center] * (1 - reduction / 100) for center in centers}

                                            # Initialize LP problem
                                            prob = LpProblem("Multiple_Centers_Meals_Optimization", LpMinimize)

                                            # Decision variables
                                            order_qty = LpVariable.dicts("Order", (centers, meals, weeks), lowBound=0, cat="Integer")
                                            inventory = LpVariable.dicts("Inventory", (centers, meals, weeks), lowBound=0, cat="Integer")
                                            order_indicator = LpVariable.dicts("OrderIndicator", (centers, meals, weeks), cat="Binary")
                                            unmet_demand = LpVariable.dicts("UnmetDemand", (centers, meals, weeks), lowBound=0, cat="Integer")

                                            # Objective function
                                            prob += lpSum(
                                                ordering_cost[meal] * order_indicator[center][meal][t] +
                                                order_qty[center][meal][t] * unit_cost[meal] +
                                                holding_cost[meal] * inventory[center][meal][t] +
                                                checkout_price[center][meal][t-1] * unmet_demand[center][meal][t]
                                                for center in centers for meal in meals for t in weeks
                                            )

                                            # Constraints
                                            for center in centers:
                                                for t in weeks:
                                                    for meal in meals:
                                                        # Inventory balance constraint
                                                        if t == 1:
                                                            prob += inventory[center][meal][t] == initial_inventory[center][meal] - demand[center][meal][t-1] + unmet_demand[center][meal][t]
                                                        else:
                                                            if t - lead_time > 0:
                                                                prob += inventory[center][meal][t] == inventory[center][meal][t-1] + order_qty[center][meal][t-lead_time] - demand[center][meal][t-1] + unmet_demand[center][meal][t] - unmet_demand[center][meal][t-1]
                                                            else:
                                                                prob += inventory[center][meal][t] == inventory[center][meal][t-1] - demand[center][meal][t-1] + unmet_demand[center][meal][t] - unmet_demand[center][meal][t-1]

                                                        # Link binary variable to order quantity
                                                        prob += order_qty[center][meal][t] <= 1000000 * order_indicator[center][meal][t]

                                                    # Weekly budget constraint with adjusted budget
                                                    prob += lpSum(order_qty[center][meal][t] * unit_cost[meal] + ordering_cost[meal] * order_indicator[center][meal][t] for meal in meals) <= adjusted_budget[center]

                                                    # Warehouse capacity constraint
                                                    prob += lpSum(inventory[center][meal][t] for meal in meals) <= warehouse_capacity[center]

                                            # Solve the optimization problem
                                            prob.solve()

                                            # Calculate evaluation metrics
                                            total_ordering_cost = 0
                                            total_holding_cost = 0
                                            total_penalty_cost = 0
                                            total_unmet_demand = 0
                                            unmet_demand_frequency = 0
                                            budget_utilization = {}

                                            for center in centers:
                                                center_spending = 0
                                                for meal in meals:
                                                    unmet_demand_value = unmet_demand[center][meal][len(weeks)].varValue
                                                    total_unmet_demand += unmet_demand_value

                                                    for t in weeks:
                                                        order_cost = ordering_cost[meal] * order_indicator[center][meal][t].varValue + order_qty[center][meal][t].varValue * unit_cost[meal]
                                                        holding_cost_week = holding_cost[meal] * inventory[center][meal][t].varValue
                                                        penalty_cost_week = checkout_price[center][meal][t-1] * unmet_demand[center][meal][t].varValue

                                                        total_ordering_cost += order_cost
                                                        total_holding_cost += holding_cost_week
                                                        total_penalty_cost += penalty_cost_week

                                                        if unmet_demand[center][meal][t].varValue > 0:
                                                            unmet_demand_frequency += 1

                                                        center_spending += order_cost

                                                budget_utilization[center] = round(center_spending / (adjusted_budget[center] * (len(weeks) - 1)), 2)

                                            # Store results for this reduction level
                                            sensitivity_results.append({
                                                "Reduction %": reduction,
                                                "Total Cost": total_ordering_cost + total_holding_cost + total_penalty_cost,
                                                "Ordering Cost": total_ordering_cost,
                                                "Holding Cost": total_holding_cost,
                                                "Penalty Cost": total_penalty_cost,
                                                "Total Unmet Demand": total_unmet_demand,
                                                "Unmet Demand Frequency": unmet_demand_frequency,
                                                "Budget Utilization": budget_utilization
                                            })

                                        # Convert results to DataFrame
                                        sensitivity_df = pd.DataFrame(sensitivity_results)

                                        # Display results
                                        st.write("Sensitivity Analysis Results:")
                                        st.dataframe(sensitivity_df)

                                        # Extracting data from the results DataFrame for plot
                                        x = sensitivity_df["Reduction %"]
                                        ordering = sensitivity_df["Ordering Cost"]
                                        holding = sensitivity_df["Holding Cost"]
                                        penalty = sensitivity_df["Penalty Cost"]
                                        total_unmet = sensitivity_df["Total Unmet Demand"]

                                        # Create a Plotly figure
                                        fig = go.Figure()

                                        # Add traces for cost components (primary y-axis)
                                        fig.add_trace(go.Scatter(x=x, y=ordering, mode="lines+markers", name="Ordering Cost", line=dict(color="skyblue")))
                                        fig.add_trace(go.Scatter(x=x, y=holding, mode="lines+markers", name="Holding Cost", line=dict(color="green", dash="dash")))
                                        fig.add_trace(go.Scatter(x=x, y=penalty, mode="lines+markers", name="Penalty Cost", line=dict(color="orange", dash="dot")))

                                        # Add a trace for unmet demand (secondary y-axis)
                                        fig.add_trace(go.Scatter(x=x, y=total_unmet, mode="lines+markers", name="Unmet Demand", line=dict(color="red"), yaxis="y2"))

                                        # Update layout for dual y-axes
                                        fig.update_layout(
                                            title="Cost Components and Unmet Demand vs Budget Reduction",
                                            xaxis=dict(title="Budget Reduction (%)"),
                                            yaxis=dict(title="Costs", titlefont=dict(color="black"), tickfont=dict(color="black")),
                                            yaxis2=dict(
                                                title="Unmet Demand",
                                                titlefont=dict(color="red"),
                                                tickfont=dict(color="red"),
                                                anchor="x",
                                                overlaying="y",
                                                side="right",
                                            ),
                                            legend=dict(x=0.5, y=-0.2, orientation="h"),
                                            template="plotly_white",
                                        )

                                        # Display the plot
                                        st.plotly_chart(fig)


                                    except ValueError:
                                        st.error("Please enter valid numeric values for budget reduction levels.")
                            else:
                                st.write("You chose not to run a sensitivity analysis.")

                            st.subheader("Simulation Analysis")
                            # Ask the user if they want to perform a simulation analysis
                            perform_simulation = st.radio("Do you want to perform a simulation analysis?", ("No", "Yes"))

                            if perform_simulation == "Yes":
                                # Input fields for scenarios and simulation number
                                simulation_scenario_input = st.text_input("Enter demand scenarios with a decimal point (e.g., 0.1, 0.2):")
                                simulation_number_input = st.number_input("Enter the number of simulations for each scenario:", min_value=1, step=1)

                                if simulation_scenario_input and simulation_number_input:
                                    # Parse inputs
                                    simulation_scenario = [float(s.strip()) for s in simulation_scenario_input.split(",")]
                                    simulation_number = int(simulation_number_input)

                                    simulated_datasets = []

                                    # Simulate demand for each scenario
                                    for scenario in simulation_scenario:
                                        for i in range(simulation_number):
                                            simulated_data = filtered_data_meal.copy()
                                            simulated_data['predicted'] = simulated_data['predicted'] * (
                                                1 + np.random.uniform(-scenario, scenario, len(filtered_data_meal))
                                            )
                                            simulated_data['scenario'] = f"Scenario: {scenario*100:.0f}% | Sim {i+1}"
                                            simulated_datasets.append(simulated_data)

                                    # Combine simulated datasets
                                    simulated_data_full = pd.concat(simulated_datasets, ignore_index=True)

                                    # Placeholder for storing simulation results
                                    simulation_results = []

                                    # Optimization loop for each scenario
                                    for scenario, scenario_data in simulated_data_full.groupby('scenario'):
                                        # Prepare demand data for the scenario
                                        demand = {
                                            center: {
                                                meal: scenario_data[
                                                    (scenario_data['center_id'] == center) & (scenario_data['meal_id'] == meal)
                                                ]['predicted'].tolist()
                                                for meal in meals
                                            }
                                            for center in centers
                                        }

                                        # Initialize LP problem
                                        prob = LpProblem("Simulation_Optimization", LpMinimize)

                                        # Decision variables
                                        order_qty = LpVariable.dicts("Order", (centers, meals, weeks), lowBound=0, cat="Integer")
                                        inventory = LpVariable.dicts("Inventory", (centers, meals, weeks), lowBound=0, cat="Integer")
                                        order_indicator = LpVariable.dicts("OrderIndicator", (centers, meals, weeks), cat="Binary")
                                        unmet_demand = LpVariable.dicts("UnmetDemand", (centers, meals, weeks), lowBound=0, cat="Integer")

                                        # Objective function: Minimize ordering + holding + penalty costs
                                        prob += lpSum(
                                            ordering_cost[meal] * order_indicator[center][meal][t] +
                                            order_qty[center][meal][t] * unit_cost[meal] +
                                            holding_cost[meal] * inventory[center][meal][t] +
                                            checkout_price[center][meal][t-1] * unmet_demand[center][meal][t]
                                            for center in centers for meal in meals for t in weeks
                                        )

                                        # Constraints
                                        for center in centers:
                                            for t in weeks:
                                                for meal in meals:
                                                    # Inventory balance constraint
                                                    if t == 1:
                                                        prob += inventory[center][meal][t] == initial_inventory[center][meal] - demand[center][meal][t-1] + unmet_demand[center][meal][t]
                                                    else:
                                                        if t - lead_time > 0:
                                                            prob += inventory[center][meal][t] == inventory[center][meal][t-1] + order_qty[center][meal][t-lead_time] - demand[center][meal][t-1] + unmet_demand[center][meal][t] - unmet_demand[center][meal][t-1]
                                                        else:
                                                            prob += inventory[center][meal][t] == inventory[center][meal][t-1] - demand[center][meal][t-1] + unmet_demand[center][meal][t] - unmet_demand[center][meal][t-1]

                                                    # Link binary variable to order quantity
                                                    prob += order_qty[center][meal][t] <= 1000000 * order_indicator[center][meal][t]

                                                # Weekly budget constraint
                                                prob += lpSum(order_qty[center][meal][t] * unit_cost[meal] + ordering_cost[meal] * order_indicator[center][meal][t] for meal in meals) <= budget[center]

                                                # Warehouse capacity constraint
                                                prob += lpSum(inventory[center][meal][t] for meal in meals) <= warehouse_capacity[center]

                                        # Solve the optimization problem
                                        prob.solve()

                                        # Collect metrics
                                        total_ordering_cost = 0
                                        total_holding_cost = 0
                                        total_penalty_cost = 0
                                        total_unmet_demand = 0
                                        unmet_demand_frequency = 0
                                        budget_utilization = {}

                                        for center in centers:
                                            center_spending = 0
                                            for meal in meals:
                                                unmet_demand_value = unmet_demand[center][meal][len(weeks)].varValue
                                                total_unmet_demand += unmet_demand_value

                                                for t in weeks:
                                                    order_cost = ordering_cost[meal] * order_indicator[center][meal][t].varValue + order_qty[center][meal][t].varValue * unit_cost[meal]
                                                    holding_cost_week = holding_cost[meal] * inventory[center][meal][t].varValue
                                                    penalty_cost_week = checkout_price[center][meal][t-1] * unmet_demand[center][meal][t].varValue

                                                    total_ordering_cost += order_cost
                                                    total_holding_cost += holding_cost_week
                                                    total_penalty_cost += penalty_cost_week

                                                    if unmet_demand[center][meal][t].varValue > 0:
                                                        unmet_demand_frequency += 1

                                                    center_spending += order_cost

                                            budget_utilization[center] = round(center_spending / (budget[center] * (len(weeks) - 1)), 2)

                                        # Store results for this simulation scenario
                                        simulation_results.append({
                                            "Scenario": scenario,
                                            "Total Cost": total_ordering_cost + total_holding_cost + total_penalty_cost,
                                            "Ordering Cost": total_ordering_cost,
                                            "Holding Cost": total_holding_cost,
                                            "Penalty Cost": total_penalty_cost,
                                            "Total Unmet Demand": total_unmet_demand,
                                            "Unmet Demand Frequency": unmet_demand_frequency,
                                            "Budget Utilization": budget_utilization
                                        })

                                    # Convert to DataFrame and display results
                                    simulation_df = pd.DataFrame(simulation_results)
                                    st.write("### Simulation Analysis Results")
                                    st.dataframe(simulation_df)


                                    # Extract relevant columns
                                    simulation_plot_data = simulation_df[['Scenario', 'Unmet Demand Frequency']]

                                    # Extract variation type from the scenario string
                                    simulation_plot_data['Scenario'] = simulation_plot_data['Scenario'].apply(lambda x: x.split(' | ')[0])

                                    # Group by Variation and calculate the mean unmet demand frequency
                                    grouped_data = simulation_plot_data.groupby('Scenario')['Unmet Demand Frequency'].mean().reset_index()

                                    # Create an interactive line plot using Plotly
                                    fig = px.line(
                                        grouped_data,
                                        x='Scenario',
                                        y='Unmet Demand Frequency',
                                        title='Unmet Demand Frequency by Scenario',
                                        labels={'Scenario': 'Scenario', 'Unmet Demand Frequency': 'Average Unmet Demand Frequency'},
                                        markers=True
                                    )

                                    # Update layout for better readability
                                    fig.update_layout(
                                        xaxis=dict(title='Scenario', tickangle=45),
                                        yaxis=dict(title='Average Unmet Demand Frequency'),
                                        title=dict(font=dict(size=14)),
                                        template='plotly_white'
                                    )


                                    # Render the plot in Streamlit
                                    st.plotly_chart(fig)

                            else:
                                st.write("You chose not to run the simulation analysis")

                    else:
                            st.warning("Exiting as per user request.")

    elif run_optimization == "No":
        st.write("You chose not to run the optimization model.")

else:
    st.warning("Please upload all three datasets to proceed.")

