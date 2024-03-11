import os
from flask import Flask, render_template, request
import pandas as pd
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import traceback
import logging


app = Flask(__name__)

# Create the 'uploads' directory if it doesn't exist
UPLOAD_FOLDER = 'uploads'
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/send_alerts', methods=['POST'])
def send_alerts():
    suspect_file = request.files['suspect_file']
    police_station_file = request.files['police_station_file']
    email = request.form['email']
    password = request.form['password']

    try:
        # Save uploaded CSV files
        suspect_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'suspect_details.csv'))
        police_station_file.save(os.path.join(app.config['UPLOAD_FOLDER'], 'police_station_details.csv'))

        # Load suspect details from CSV
        suspect_data = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'suspect_details.csv'))

        # Load police station details from CSV
        police_station_data = pd.read_csv(os.path.join(app.config['UPLOAD_FOLDER'], 'police_station_details.csv'))

        # Email configuration
        login_acc = email
        login_pass = password

        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(login_acc, login_pass)

        # Iterate through suspect details
        for index, suspect in suspect_data.iterrows():
            # Extract suspect information
            first_name = suspect['first_name']
            middle_name = suspect['middle_name']
            surname = suspect['surname']
            phone = suspect['phone']
            email = suspect['email']
            address = suspect['address']
            dob = suspect['date_of_birth']
            pincode = suspect['pincode']

            # Find matching police station details based on pincode
            matching_police_station = police_station_data.loc[police_station_data['pincode'] == pincode]

            # If matching police station found
            if not matching_police_station.empty:
                # Prepare email message
                msg = MIMEMultipart()
                msg['From'] = login_acc
                msg['Subject'] = "Suspect Alert: " + first_name + " " + surname

                # Construct email body
                email_body = f"Suspect details:\nName: {first_name} {middle_name} {surname}\nPhone: {phone}\nEmail: {email}\nAddress: {address}\nDate of Birth: {dob}\nPincode: {pincode}\n"
                msg.attach(MIMEText(email_body, 'plain'))

                # Send email to matching police station
                for index, station in matching_police_station.iterrows():
                    police_station_email = station['email']
                    msg['To'] = police_station_email
                    server.sendmail(login_acc, police_station_email, msg.as_string())
                    print(f"Email sent to {police_station_email} regarding suspect: {first_name} {surname}")

        # Quit SMTP server
        server.quit()

        return render_template('success.html')

    except Exception as e:
        logging.error(traceback.format_exc())
        return render_template('error.html', error=str(e))

if __name__ == '__main__':
    app.run(debug=True)
