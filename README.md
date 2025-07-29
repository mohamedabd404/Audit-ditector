# RES-VA Call Audit Tool

A professional call audit application for analyzing call dispositions and flagging issues.

## Features

- **Login System**: Secure authentication for authorized users
- **Call Analysis**: Automatic flagging of problematic calls
- **Agent Summary**: Overview of agent performance with total dead calls and unknown calls
- **Visual Analytics**: Pie charts showing call disposition breakdown
- **Real-time Filtering**: Filter by agent and disposition
- **Data Export**: Download filtered results and summaries

## Installation

1. Clone this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Run the app:
   ```bash
   streamlit run audit2_app.py
   ```

## Usage

1. Login with authorized credentials
2. Upload your call log CSV file
3. Use filters to analyze specific agents or dispositions
4. View summaries and download results

## File Structure

- `audit2_app.py` - Main Streamlit application
- `main.py` - Recording download script
- `requirements.txt` - Python dependencies
- `call_log.csv` - Sample data file

## Deployment

This app can be deployed on Streamlit Cloud, Heroku, or any platform supporting Python web applications. 