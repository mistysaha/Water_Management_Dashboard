from flask import Flask, render_template, request, redirect
import pandas as pd
import os
import datetime

app = Flask(__name__)

# reads both csv files 
def load_data():
    df = pd.read_csv('water_quality_results.csv')
    leak_df = pd.read_csv('leakage_results.csv')
    return df, leak_df

# ---------- USER PAGE ----------
@app.route('/')
def user_page():
    df, leak_df = load_data()
    states = sorted(df['State Name'].unique())
    selected_state = request.args.get('state', states[0])
    
    state_data = df[df['State Name'] == selected_state]
    good_count = int((state_data['Water_Quality_Label'] == 'Good').sum())
    poor_count = int((state_data['Water_Quality_Label'] == 'Poor').sum())
    
    summary = f"{selected_state} has {len(state_data)} monitored locations — {good_count} Good, {poor_count} Poor."
    
    # leakage data filtered to selected state, same as manager page
    state_leak_data = leak_df[leak_df['State Name'] == selected_state]
    high_risk_count = int((state_leak_data['Risk_Level'] == 'High Risk').sum())
    risk_counts = state_leak_data['Risk_Level'].value_counts().to_dict()
    
    return render_template('user.html', states=states, selected_state=selected_state,
                           locations=state_data.to_dict('records'), summary=summary,
                           good_count=good_count, poor_count=poor_count,
                           leak_data=state_leak_data.to_dict('records'),
                           high_risk_count=high_risk_count,
                           risk_low=risk_counts.get('Low Risk', 0),
                           risk_medium=risk_counts.get('Medium Risk', 0),
                           risk_high=risk_counts.get('High Risk', 0))

# ---------- ALERT SUBMISSION ----------
@app.route('/submit_alert', methods=['POST'])
def submit_alert():
    # grab the values the citizen typed into the alert form
    location = request.form['location']
    coordinates = request.form['coordinates']
    issue = request.form['issue']

    # build one new row for this alert, with a timestamp and default status
    new_alert = pd.DataFrame([{
        'Location': location, 'Coordinates': coordinates, 'Issue': issue,
        'Timestamp': datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S'), 'Status': 'New'
    }])

    # if alerts.csv already exists, add this as a new row (no header repeated)
    # if it doesn't exist yet, create it fresh with header
    if os.path.exists('alerts.csv'):
        new_alert.to_csv('alerts.csv', mode='a', header=False, index=False)
    else:
        new_alert.to_csv('alerts.csv', index=False)

    # redirect back to the user page, adding ?submitted=true so the success message shows
    return redirect('/?submitted=true')


# ---------- MANAGER PAGE ----------
@app.route('/manager')
@app.route('/manager')
def manager_page():
    df, leak_df = load_data()
    states = sorted(df['State Name'].unique())
    selected_state = request.args.get('state', states[0])
    
    state_data = df[df['State Name'] == selected_state]
    state_leak_data = leak_df[leak_df['State Name'] == selected_state]  # filter leak data too
    
    alerts = pd.read_csv('alerts.csv') if os.path.exists('alerts.csv') else pd.DataFrame()
    
    high_risk_count = int((state_leak_data['Risk_Level'] == 'High Risk').sum())
    risk_counts = state_leak_data['Risk_Level'].value_counts().to_dict()
    
    return render_template('manager.html', states=states, selected_state=selected_state,
                           locations=state_data.to_dict('records'), 
                           alerts=alerts.to_dict('records'),
                           leak_data=state_leak_data.to_dict('records'),
                           high_risk_count=high_risk_count,
                           risk_low=risk_counts.get('Low Risk', 0),
                           risk_medium=risk_counts.get('Medium Risk', 0),
                           risk_high=risk_counts.get('High Risk', 0))

if __name__ == '__main__':
    app.run(debug=True)