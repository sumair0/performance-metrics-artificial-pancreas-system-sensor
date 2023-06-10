# Extracting Time Series Properties of Glucose Levels in Artificial Pancreas

## Introduction
This project aims to extract several performance metrics of an Artificial Pancreas system from sensor data. The focus is on the Medtronic 670G system, which consists of a continuous glucose monitor (CGM) and the Guardian Sensor (12). The sensor collects blood glucose measurements every 5 minutes, and the data is used to compute various statistical measures.

## Objectives

Extract feature data from a dataset.
Synchronize data from two sensors.
Compute and report overall statistical measures from the data.
## Technology Requirements

Python 3.6 to 3.8 (do not use 3.9).
scikit-learn==0.21.2
pandas==0.25.1
Python pickle
## Project Description
This project focuses on the analysis of the Artificial Pancreas medical control system, specifically the Medtronic 670G system. The system comprises a continuous glucose monitor (CGM) and the Guardian Sensor (12), which collects blood glucose measurements every 5 minutes.

The project involves extracting several metrics from the sensor data, including the percentage of time in hyperglycemia, percentage of time in hyperglycemia critical, percentage of time in range, percentage of time in range secondary, percentage of time in hypoglycemia level 1, and percentage of time in hypoglycemia level 2. These metrics are computed for different time intervals: daytime (6 am to midnight), overnight (midnight to 6 am), and the whole day (12 am to 12 am).

The project also includes analyzing the data based on two cases: manual mode and auto mode.

