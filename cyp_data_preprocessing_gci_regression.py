# -*- coding: utf-8 -*-
"""CYP_Data_Preprocessing_GCI_Regression.ipynb

Automatically generated by Colab.

Original file is located at
    https://colab.research.google.com/drive/1nzEc-RCS0LE2004dRcAXohh07cUEriLb
"""

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
import torch
import torch.nn as nn
import torch.optim as optim
from torch.utils.data import DataLoader, TensorDataset, random_split

!ls

yield_files = [
    '2020_calibrated_yield.csv',
    '2021_calibrated_yield.csv GCI_2021.csv',
    '2022_calibrated_yield.csv GCI_2022.csv',
    '2023_calibrated_yield.csv GCI_2023.csv'
]

ndvi_files = [
    'NDVI_2020.csv',
    'NDVI_2021.csv',
    'NDVI_2022.csv',
    'NDVI_2023.csv'
]

gci_files = [
    'GCI_2020.csv',
    'GCI_2021.csv',
    'GCI_2022.csv',
    'GCI_2023.csv'
]

agri_dates = {
    2020: {'seeding': '2020-02-29', 'defoliation': '2020-07-13', 'harvest': '2020-08-03'},
    2021: {'seeding': '2021-02-27', 'defoliation': '2021-07-27', 'harvest': '2021-08-13'},
    2022: {'seeding': '2022-03-15', 'defoliation': '2022-07-19', 'harvest': '2022-08-04'},
    2023: {'seeding': '2023-03-05', 'defoliation': '2023-07-18', 'harvest': '2023-08-01'}
}

d = pd.read_csv('GCI_2020.csv')

d.head()

len(d.columns)

y = pd.read_csv(yield_files[0])

len(y)

y.head()

d.columns

d.columns = [d.columns[0]] + list(pd.to_datetime(d.columns[1:], format='%Y%m%d'))

d.columns

date_columns = d.columns[1:]
d.columns = [d.columns[0]] + list(pd.to_datetime(date_columns))
d_transposed = d.set_index('FID').T
biweekly_index = pd.date_range(start=d_transposed.index.min(), end=d_transposed.index.max(), freq='3D')
d_biweekly = d_transposed.reindex(biweekly_index).interpolate(method='linear')
d_biweekly = d_biweekly.T.reset_index()
d_biweekly.columns = ['FID'] + list(biweekly_index)
print(d_biweekly.head())

d_biweekly.iloc[0][1:]



"""# Data Preprocessing - Final"""

agri_dates = {
    2020: {'seeding': '2020-02-29'},
    2021: {'seeding': '2021-02-27'},
    2022: {'seeding': '2022-03-15'},
    2023: {'seeding': '2023-03-05'}
}

gci_files = [
    'GCI_2020.csv',
    'GCI_2021.csv',
    'GCI_2022.csv',
    'GCI_2023.csv'
]

def process_gci_with_intervals(gci_files, agri_dates, interval_size=3, total_days=250):
    processed_data = {}

    for year, file_ in zip(agri_dates.keys(), gci_files):
        df = pd.read_csv(file_)
        df.columns = ['FID'] + list(pd.to_datetime(df.columns[1:], format='%Y%m%d'))

        seeding_date = pd.to_datetime(agri_dates[year]['seeding'])
        intervals = [
            (seeding_date + pd.Timedelta(days=i * interval_size),
             seeding_date + pd.Timedelta(days=(i + 1) * interval_size - 1))
            for i in range(total_days // interval_size)
        ]

        print(intervals)

        interval_columns = [f'Interval {i+1}' for i in range(len(intervals))]
        interval_df = pd.DataFrame(columns=['FID'] + interval_columns)
        interval_df['FID'] = df['FID']

        for i, (start, end) in enumerate(intervals):
            mask = (df.columns[1:] >= start) & (df.columns[1:] <= end)

            interval_values = df.iloc[:, 1:].loc[:, mask]

            interval_df[f'Interval {i+1}'] = interval_values.max(axis=1, skipna=True)

        processed_data[year] = interval_df

    return processed_data

processed_gci = process_gci_with_intervals(gci_files, agri_dates)

agri_dates = {
    2020: {'seeding': '2020-02-29'},
    2021: {'seeding': '2021-02-27'},
    2022: {'seeding': '2022-03-15'},
    2023: {'seeding': '2023-03-05'}
}

gci_files = [
    'GCI_2020.csv',
    'GCI_2021.csv',
    'GCI_2022.csv',
    'GCI_2023.csv'
]

#
def process_gci_simple(gci_files, agri_dates, total_days=180):
    processed_data = {}
    for year, file in zip(agri_dates.keys(), gci_files):
        print(year)
        df = pd.read_csv(file)
        df.columns = ['FID'] + list(pd.to_datetime(df.columns[1:], format='%Y%m%d'))
        seeding_date = pd.to_datetime(agri_dates[year]['seeding'])

        # Enforce presence of seeding date in the dataframe
        # Find the nearest previous date and substitute its value
        date_cols = df.columns[1:]
        print(seeding_date)
        if seeding_date not in date_cols:
            if seeding_date > date_cols[0]:
              # Learn: df.columns.get_loc(seeding_date) - 1: index of seeding date col
              # Learn: result = [expression for item in iterable if condition]
              previous_date = max([date for date in date_cols if date < seeding_date])
              df[seeding_date] = df[previous_date]
              df = pd.concat([df.iloc[:, :1], df.iloc[:, 1:].sort_index(axis=1)], axis=1)
            else:
              # Learn: this fills the entire col with 0s
              df[seeding_date] = 0
              # Learn Later: Complex Concats
              df = pd.concat([df.iloc[:, :1], df.iloc[:, 1:].sort_index(axis=1)], axis=1)

        target_dates = pd.date_range(start=seeding_date, periods=total_days)

        target_df = pd.DataFrame(columns=['FID'] + list(target_dates))
        target_df['FID'] = df['FID']

        df_transposed = df.set_index('FID').T
        df_transposed.index = pd.to_datetime(df_transposed.index)

        reindexed = df_transposed.reindex(target_dates)

        interpolated = reindexed.interpolate(method='linear', axis=0)
        interpolated.loc[target_dates < df_transposed.index.min()] = 0
        interpolated.loc[target_dates > df_transposed.index.max()] = 0

        final_df = interpolated.T.reset_index()
        final_df.columns = ['FID'] + list(target_dates)

        processed_data[year] = final_df

    return processed_data

processed_gci = process_gci_simple(gci_files, agri_dates)

processed_gci[2020].head()

processed_gci[2021].head()

processed_gci[2022].head()

gci_row = processed_gci[2022].iloc[0, 1:]

gci_dates = processed_gci[2022].columns[1:]

plt.figure(figsize=(10, 6))
plt.plot(gci_dates, gci_row, marker='o', color='orange', label='GCI Values')
plt.title("GCI Values for First Row (2020)", fontsize=14)
plt.xlabel("Date", fontsize=12)
plt.ylabel("GCI", fontsize=12)
plt.xticks(rotation=45)
plt.grid(True)
plt.legend()
plt.tight_layout()
plt.show()





df_2020 = pd.read_csv('GCI_2022.csv')

df_2020.columns = ['FID'] + list(pd.to_datetime(df_2020.columns[1:], format='%Y%m%d'))

plt.figure(figsize=(12, 6))
plt.plot(df_2020.columns[1:], df_2020.iloc[0, 1:], marker='o', label='GCI Values (Grid 1)', color='orange')

plt.title("GCI Values from Original GCI_2020.csv (Grid 1)", fontsize=14)
plt.xlabel("Date", fontsize=12)
plt.ylabel("GCI Value", fontsize=12)
plt.xticks(rotation=45)
plt.grid(True)
plt.legend()
plt.tight_layout()

plt.show()

processed_gci[2020].shape

processed_gci[2021].shape

processed_gci[2022].shape

common_columns = ['FID'] + [f'Day {i}' for i in range(1, 181)]

for year in [2020, 2021, 2022]:
    processed_gci[year].columns = common_columns
    # processed_gci[year] = processed_gci[year].reindex(columns=common_columns, fill_value=np.nan)

df_combined = pd.concat(
    [processed_gci[2020], processed_gci[2021], processed_gci[2022]],
    axis=0,
    ignore_index=True
)

print(df_combined.isnull().sum())
print(df_combined.head())
print("Shape of df_combined:", df_combined.shape)

processed_gci[2022].isnull().sum()

df_combined.isnull().sum()

df_combined = df_combined.fillna(0)

def prepare_data(df, input_size):
    data = df.iloc[:, 1:].values
    inputs = data[:, :input_size]
    targets = data[:, input_size:]
    return torch.tensor(inputs, dtype=torch.float32), torch.tensor(targets, dtype=torch.float32)

input_size = 35
output_size = 180 - input_size
batch_size = 64
epochs = 20

x, y = prepare_data(df_combined, input_size)
dataset = TensorDataset(x, y)

train_size = int(0.8 * len(dataset))
val_size = len(dataset) - train_size
train_dataset, val_dataset = random_split(dataset, [train_size, val_size])

train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)

class TimeSeriesPredictor(nn.Module):
    def __init__(self, input_size, output_size, dropout_rate=0.15):
        super(TimeSeriesPredictor, self).__init__()
        self.fc1 = nn.Linear(input_size, 3)
        self.dropout1 = nn.Dropout(dropout_rate)
        self.fc2 = nn.Linear(3, 15)
        self.dropout2 = nn.Dropout(dropout_rate)
        self.fc3 = nn.Linear(15, output_size)

    def forward(self, x):
        x = torch.relu(self.fc1(x))
        x = self.dropout1(x)
        x = torch.relu(self.fc2(x))
        x = self.dropout2(x)
        x = self.fc3(x)
        return x


model = TimeSeriesPredictor(input_size, output_size)
criterion = nn.MSELoss()
optimizer = optim.Adam(model.parameters(), lr=0.001)

train_losses = []
val_losses = []

for epoch in range(epochs):
    model.train()
    total_loss = 0
    for batch_x, batch_y in train_loader:
        optimizer.zero_grad()
        predictions = model(batch_x)
        loss = criterion(predictions, batch_y)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()

    train_loss = total_loss / len(train_loader)
    train_losses.append(train_loss)

    model.eval()
    val_loss = 0
    with torch.no_grad():
        for val_x, val_y in val_loader:
            val_predictions = model(val_x)
            val_loss += criterion(val_predictions, val_y).item()

    val_loss = val_loss / len(val_loader)
    val_losses.append(val_loss)

    print(f"Epoch {epoch+1}/{epochs}, Train Loss: {train_loss:.4f}, Val Loss: {val_loss:.4f}")

plt.figure(figsize=(8, 5))
plt.plot(range(1, epochs + 1), train_losses, label='Train Loss', marker='o')
plt.plot(range(1, epochs + 1), val_losses, label='Validation Loss', marker='s')
plt.xlabel('Epochs')
plt.ylabel('Loss')
plt.title('Train Loss vs Validation Loss')
plt.legend()
plt.grid()
plt.show()

sample_index = np.random.randint(0, len(val_dataset))
sample_input, sample_target = val_dataset[sample_index]
sample_input = sample_input.numpy()
sample_target = sample_target.numpy()

model.eval()
with torch.no_grad():
    predicted_output = model(torch.tensor(sample_input).unsqueeze(0)).squeeze(0).numpy()

plt.figure(figsize=(10, 6))

plt.plot(range(input_size), sample_input, label="Input (Observed)", color="blue", linewidth=2)
plt.plot(range(input_size, input_size + len(sample_target)), sample_target, label="Ground Truth (Target)", color="green", linewidth=2)
plt.plot(range(input_size, input_size + len(predicted_output)), predicted_output, label="Predicted (Model Output)", color="orange", linestyle="dashed", linewidth=2)
plt.axvline(x=input_size - 1, color="red", linestyle="dotted", label="Input/Output Boundary")

plt.title("GCI Prediction - Val Data Sample - (Inputs and Outputs)")
plt.xlabel("Time Steps")
plt.ylabel("Value")
plt.legend()
plt.grid()
plt.show()

def preprocess_gci_with_rules(file_path, seeding_date, total_days=180):
    df = pd.read_csv(file_path)

    df.columns = ['FID'] + list(pd.to_datetime(df.columns[1:], format='%Y%m%d'))

    seeding_date = pd.to_datetime(seeding_date)
    target_dates = pd.date_range(start=seeding_date, periods=total_days)

    df_transposed = df.set_index('FID').T
    df_transposed.index = pd.to_datetime(df_transposed.index)

    reindexed = df_transposed.reindex(target_dates)

    reindexed.loc[target_dates < df_transposed.index.min()] = 0

    interpolated = reindexed.interpolate(method='linear', axis=0)

    interpolated.loc[target_dates > df_transposed.index.max()] = 0

    final_df = interpolated.T.reset_index()
    final_df.columns = ['FID'] + list(target_dates)

    return final_df

agri_dates = {
    2023: {'seeding': '2023-03-05'}
}

file_path = 'GCI_2023.csv'
seeding_date_2023 = agri_dates[2023]['seeding']
processed_gci_2023 = preprocess_gci_with_rules(file_path, seeding_date_2023)

print("Processed GCI for 2023:")
print(processed_gci_2023.head())

processed_gci_2023.fillna(0, inplace=True)

def prepare_testing_data(df, input_size):
    data = df.iloc[:, 1:].values
    test_inputs = data[:, :input_size]
    test_targets = data[:, input_size:]
    return torch.tensor(test_inputs, dtype=torch.float32), torch.tensor(test_targets, dtype=torch.float32)


test_x, test_y = prepare_testing_data(processed_gci_2023, input_size)

model.eval()

with torch.no_grad():
    predictions = model(test_x).numpy()
    ground_truth = test_y.numpy()

sample_index = 2000 #np.random.randint(0, len(test_x))
sample_input = test_x[sample_index].numpy()
sample_target = test_y[sample_index].numpy()

model.eval()
with torch.no_grad():
    predicted_output = model(torch.tensor(sample_input).unsqueeze(0)).squeeze(0).numpy()

print("Sample Input:", sample_input)
print("Sample Target (Ground Truth):", sample_target)
print("Predicted Output:", predicted_output)

plt.figure(figsize=(10, 6))

plt.plot(range(input_size), sample_input, label="Input (Observed)", color="blue", linewidth=2)

plt.plot(range(input_size, input_size + len(sample_target)), sample_target, label="Ground Truth (Target)", color="green", linewidth=2)

plt.plot(range(input_size, input_size + len(predicted_output)), predicted_output, label="Predicted (Model Output)", color="orange", linestyle="dashed", linewidth=2)
plt.axvline(x=input_size - 1, color="red", linestyle="dotted", label="Input/Output Boundary")
plt.title("GCI Prediction on Test Data")
plt.xlabel("Time Steps")
plt.ylabel("GCI Value")
plt.legend()
plt.grid()
plt.show()

