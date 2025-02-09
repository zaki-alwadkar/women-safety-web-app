import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from twilio.rest import Client
import requests

# Load crime data
file_path = r'C:\Users\Hp\Desktop\hackathon\hack2\crime-safety-app\crime_data.csv'
crime_data = pd.read_csv(file_path)

# Your Twilio credentials (replace with your actual credentials)
account_sid = 'ACf8306e0bc7d47e863744a6f0e97f54f5'
auth_token = '3d09039190e8415c199b1d6250cb9f58'
twilio_number = '+14159688441'

# Initialize Twilio client
client = Client(account_sid, auth_token)

# LocationIQ API access token
locationiq_token = 'pk.16bbd408afc2077038d924a78dd58103'

# Function to get latitude and longitude from the district name using LocationIQ API
def get_lat_lon_locationiq(district_name, token):
    try:
        if district_name.lower() == "total" or not district_name.strip():
            st.warning(f"Skipping invalid district name: {district_name}")
            return None, None
        url = f"https://us1.locationiq.com/v1/search.php?key={token}&q={district_name}, India&format=json"
        response = requests.get(url)
        data = response.json()
        if data:
            lat = data[0]['lat']
            lon = data[0]['lon']
            return float(lat), float(lon)
        else:
            st.warning(f"No location found for {district_name}")
            return None, None
    except Exception as e:
        st.error(f"Error fetching coordinates for {district_name}: {e}")
        return None, None

# Function to make a call
def make_call(to_number, from_number):
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url='http://demo.twilio.com/docs/voice.xml'
    )
    return call.sid

# Function for location tracking and adding zones to the map
def get_location_map(lat, lon, danger_zones, safe_zones):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    for zone in danger_zones:
        folium.Marker([zone['lat'], zone['lon']], popup=f"Danger Zone: {zone['name']}", icon=folium.Icon(color='red')).add_to(m)
    for zone in safe_zones:
        folium.Marker([zone['lat'], zone['lon']], popup=f"Safe Zone: {zone['name']}", icon=folium.Icon(color='green')).add_to(m)
    return m

# Function to classify zones based on total crime
def classify_zones(data, threshold=5000):
    danger_zones = []
    safe_zones = []
    for _, row in data.iterrows():
        lat, lon = get_lat_lon_locationiq(row['District'], locationiq_token)
        if lat is not None and lon is not None:
            if row['Total Cognizable IPC crimes'] > threshold:
                danger_zones.append({"name": row['District'], "lat": lat, "lon": lon})
            else:
                safe_zones.append({"name": row['District'], "lat": lat, "lon": lon})
    return danger_zones, safe_zones

# Streamlit app configuration
st.set_page_config(page_title="Women Safety App", layout="wide")

# Custom CSS for background and themed look
st.markdown("""
    <style>
        /* Set a background image or color */
        .stApp {
            background: url('https://www.example.com/background-image.jpg') no-repeat center center fixed; 
            background-size: cover;
            background-color: #F3E5F5; /* Fallback color if image not available */
        }
        
        .main-title {
            text-align: center;
            font-size: 36px;
            color: #E91E63;
            font-weight: bold;
            margin-top: 20px;
        }
        .section-title {
            font-size: 24px;
            color: #673AB7;
            margin-top: 20px;
            border-bottom: 2px solid #FF4081;
            padding-bottom: 10px;
        }
        .sos-btn, .btn, .call-btn, .search-btn {
            color: white;
            padding: 15px 30px;
            text-align: center;
            font-size: 20px;
            cursor: pointer;
            border-radius: 50px;
            margin: 20px auto;
            display: inline-block;
            width: 100%;
        }
        .sos-btn {
            background-color: #FF5252;
        }
        .sos-btn:hover {
            background-color: #E53935;
        }
        .btn, .call-btn, .search-btn {
            background-color: #4CAF50;
        }
        .btn:hover, .call-btn:hover, .search-btn:hover {
            background-color: #388E3C;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px 0;
            background-color: #F3E5F5;
            color: #673AB7;
        }
        .footer img {
            width: 40px;
            height: auto;
            margin: 0 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# Function to display SOS button and handle the call action
def display_sos_button():
    to_number = st.text_input("Enter the phone number for emergency SOS call", "+919353564074", key="sos_number")
    if st.button("SOS Call", key="sos_call"):
        if to_number:
            try:
                call_sid = make_call(to_number, twilio_number)
                st.success(f"Emergency SOS call initiated successfully! Call SID: {call_sid}")
            except Exception as e:
                st.error(f"Error initiating call: {e}")
        else:
            st.error("Please enter a valid phone number.")

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Login", "Register", "Landing Page", "Search Zones", "SOS"])

# --- Login Page ---
if page == "Login":
    st.markdown("<div class='main-title'>Login</div>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    if st.button("Login", key="login"):
        if username and password:
            st.success("Logged in successfully!")
        else:
            st.error("Please enter both username and password.")
    display_sos_button()

# --- Registration Page ---
elif page == "Register":
    st.markdown("<div class='main-title'>Register</div>", unsafe_allow_html=True)
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    if st.button("Register", key="register"):
        if new_username and new_password:
            st.success("Registration successful!")
        else:
            st.error("Please enter both username and password.")
    display_sos_button()

# --- Landing Page ---
elif page == "Landing Page":
    st.markdown("<div class='main-title'>Welcome to the Women Safety App</div>", unsafe_allow_html=True)
    
    st.markdown("""
        <div class="image-section">
            <img src="https://example.com/large-image.jpg" alt="Safety Image" style="width:80%; margin:auto; display:block;">
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='button-section'>", unsafe_allow_html=True)

    if st.button("SOS Call", key="landing_sos"):
        display_sos_button()

    if st.button("SMS Alert", key="landing_sms"):
        st.success("Sending SMS alert... (Placeholder)")

    if st.button("Buy Product", key="landing_buy"):
        st.success("Redirecting to product page... (Placeholder)")

    st.markdown("</div>", unsafe_allow_html=True)

# --- Search Zones Page ---
elif page == "Search Zones":
    st.markdown("<div class='main-title'>Search for Danger and Safe Zones</div>", unsafe_allow_html=True)
    district_name = st.text_input("Enter district name")
    if district_name:
        district_data = crime_data[crime_data['District'].str.contains(district_name, case=False)]
        if not district_data.empty:
            danger_zones, safe_zones = classify_zones(district_data)
            st.markdown("<div class='section-title'>Danger Zones</div>", unsafe_allow_html=True)
            for zone in danger_zones:
                st.write(f"**{zone['name']}**")
            st.markdown("<div class='section-title'>Safe Zones</div>", unsafe_allow_html=True)
            for zone in safe_zones:
                st.write(f"**{zone['name']}**")
            m = get_location_map(28.7041, 77.1025, danger_zones, safe_zones)
            st_folium(m, width=700, height=500)
        else:
            st.error(f"No data found for {district_name}")
    display_sos_button()

# --- SOS Page ---
elif page == "SOS":
    st.markdown("<div class='main-title'>SOS Alert</div>", unsafe_allow_html=True)
    display_sos_button()

# Footer Menu
st.markdown("""
    <div class="footer">
        <p>Stay Safe! Your safety is our priority.</p>
    </div>
    """, unsafe_allow_html=True)
