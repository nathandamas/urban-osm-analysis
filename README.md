![Project Logo](https://github.com/nathandamas/urban-osm-analysis/blob/master/images/osm_urban%20(Custom).png)

# Urban OSM Analysis

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


## Usage
1. Clone the Repository:
```bash
git clone https://github.com/yourusername/osm-contribution-dynamics-curitiba.git
cd osm-contribution-dynamics-curitiba
```

2. Configure Paths:
- Ensure that your GeoJSON file (grid of 1 km² cells) is placed in the correct directory and update the geojson_path variable in the code if necessary.
3. Run the Scripts:
- Execute the Python scripts to collect data from the ohsome API and generate visualizations:
```bash
python your_script.py
```
- The figures will be saved in the specified SAVE_DIRECTORY.


## Running the Application
This project is designed for a local environment. Once you run the main script, it will:

- Query the ohsome API for selected grid cells (IDs 523 and 557) over two defined time intervals.
- Merge the data, calculate persistence metrics, and generate time series plots.
- Save output figures (e.g., merged deletion plots) in the designated directory.

<!-- CONTRIBUTING -->
## Contributing

Contributions are what make the open source community such an amazing place to learn, inspire, and create. Any contributions you make are **greatly appreciated**.

If you have a suggestion that would make this better, please fork the repo and create a pull request. You can also simply open an issue with the tag "enhancement".
Don't forget to give the project a star! Thanks again! For major changes, open an issue first to discuss what you would like to change.

1. Fork the Project
2. Create your Feature Branch (`git checkout -b feature/AmazingFeature`)
3. Commit your Changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the Branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request


## License

This project is licensed under the MIT License.

## Authors

## Acknowledgments
- Thanks to the Heidelberg Institute for Geoinformation Technology for developing the ohsome API.
- Special thanks to all volunteer mappers contributing to OpenStreetMap.
- Inspiration drawn from related research on urban mapping and OSM data quality.
