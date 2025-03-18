![Project Logo](https://github.com/nathandamas/your-repo/assets/your-logo-image)

# OSM Contribution Dynamics in Curitiba

![License: MIT](https://img.shields.io/badge/license-MIT-blue)
![Status: In Development](http://img.shields.io/static/v1?label=STATUS&message=IN%20DEVELOPMENT&color=yellow&style=for-the-badge)

This repository contains Python scripts and analyses for investigating the temporal dynamics of OpenStreetMap (OSM) contributions in Curitiba, Brazil. The project focuses on evaluating data persistence (creations, modifications, and deletions) via the ohsome API and logistic regression modeling, providing insights into urban mapping growth for smart city initiatives.

## Table of Contents

- [About the Project](#about-the-project)
- [Features](#features)
- [Requirements](#requirements)
- [Usage](#usage)
- [Running the Application](#running-the-application)
- [Contributing](#contributing)
- [License](#license)
- [Authors](#authors)
- [Acknowledgments](#acknowledgments)

## About the Project

This project analyzes OpenStreetMap contributions in Curitiba, emphasizing data persistence by examining creations, modifications, and deletions. It uses historical data retrieved via the ohsome API, and employs logistic regression modeling to assess mapping saturation. The project aims to support urban planning and sustainability monitoring by identifying stable mapping trends.

**Key Components:**
- Automated data collection from the ohsome API.
- Processing of spatial data using GeoPandas.
- Visualization of time series and mapping growth via Matplotlib.
- Analysis of persistence metrics to quantify OSM data stability.

## Features

- **Multi-Interval Data Query:** Handles multiple time intervals to overcome API query limits.
- **Automated Data Processing:** Uses Python (requests, pandas, geopandas, matplotlib) to extract and visualize OSM contribution data.
- **Persistence Analysis:** Calculates the ratio of surviving contributions to assess data stability.
- **Logistic Regression Modeling:** Evaluates mapping growth saturation in urban cells.
- **Reproducible Workflow:** All code and scripts are designed for ease of replication.

## Requirements

To run this project, you will need:

- Python 3.11
- Required libraries:  
  ```bash
  pip install requests geopandas pandas matplotlib
