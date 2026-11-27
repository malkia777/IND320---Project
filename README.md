# IND320 – Reservoir and Energy Data

This project explores Norwegian reservoir filling levels, cross-border
electricity transfers and weather data using a Jupyter Notebook and
a Streamlit app.

## Streamlit app

[Open the app](https://ind320---project-na9lbm8ud4jhtvejiciia6.streamlit.app/)

The app includes:
- Tables and plots of reservoir filling levels from the NVE API.
- Cross-border electricity transfers read from MongoDB.
- STL decomposition and a spectrogram of reservoir filling levels.
- Temperature outlier detection using DCT/SPC and Local Outlier Factor (LOF).

## Data sources

- [NVE Magasinstatistikk](https://www.nve.no/energi/analyser-og-statistikk/magasinstatistikk/)
- [NVE Atlas](https://atlas.nve.no/)
- [ENTSO-E Transparency Platform](https://transparency.entsoe.eu/)
- [Open-Meteo](https://open-meteo.com/)

Reservoir data are downloaded directly from NVE. Electricity transfer
data are downloaded in the notebook, stored in Cassandra, extracted
using Spark and uploaded to MongoDB.

The weather analysis uses hourly ERA5 data for a sampled location
in NO3 during 2024, aggregated into daily averages.

## Run the app locally

Install the required packages:

    pip install -r requirements.txt

Run the main Streamlit file:

    streamlit run main.py

Replace main.py with your entry-point filename if it is different.

## Secrets

The electricity transfer page requires a MongoDB connection.
Create .streamlit/secrets.toml locally:

    [mongo]
    uri = "YOUR_MONGODB_CONNECTION_STRING"

Keep secrets.toml out of GitHub. For deployment, add the MongoDB
connection string to the app's Streamlit secrets settings.

The ENTSO-E token is used in the notebook to download electricity
transfer data. It is not needed by the Streamlit app, which reads
the uploaded data from MongoDB.

## Notebook

The Jupyter Notebook contains the data preparation, analysis,
plots, project log and description of AI usage. Running the full
data pipeline requires local Cassandra and Spark, a MongoDB
connection and an ENTSO-E token.

## AI usage

ChatGPT was used to explain methods, debug code, interpret plots,
adapt notebook code for Streamlit and assist with writing.
GitHub Copilot was used for code suggestions in VS Code.

## Development

Each project part is developed on a separate branch. Changes are
merged into main after peer review and teacher feedback.