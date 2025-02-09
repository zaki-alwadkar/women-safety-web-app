import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium
from twilio.rest import Client
import requests
import xml.etree.ElementTree as ET
import os

# --- Paths and Credentials ---
file_path = r'C:\Users\Hp\Desktop\hackathon\hack2\crime-safety-app\crime_data.csv'
user_file = r'C:\Users\Hp\Desktop\hackathon\hack2\crime-safety-app\users.xml'
crime_data = pd.read_csv(file_path)
account_sid = 'ACf8306e0bc7d47e863744a6f0e97f54f5'
auth_token = '3d09039190e8415c199b1d6250cb9f58'
twilio_number = '+14159688441'
client = Client(account_sid, auth_token)
locationiq_token = 'pk.16bbd408afc2077038d924a78dd58103'

# --- XML User Management Functions ---
def create_user_file(file_path):
    if not os.path.exists(file_path):
        root = ET.Element("users")
        tree = ET.ElementTree(root)
        tree.write(file_path)

def add_user_to_xml(file_path, username, password):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for user in root.findall('user'):
        if user.find('username').text == username:
            return False
    
    user = ET.SubElement(root, "user")
    ET.SubElement(user, "username").text = username
    ET.SubElement(user, "password").text = password
    tree.write(file_path)
    return True

def authenticate_user(file_path, username, password):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for user in root.findall('user'):
        if user.find('username').text == username and user.find('password').text == password:
            return True
    return False

def user_exists(file_path, username):
    tree = ET.parse(file_path)
    root = tree.getroot()
    
    for user in root.findall('user'):
        if user.find('username').text == username:
            return True
    return False

create_user_file(user_file)

# --- Twilio SOS Call Function ---
def make_call(to_number, from_number):
    call = client.calls.create(
        to=to_number,
        from_=from_number,
        url='http://demo.twilio.com/docs/voice.xml'
    )
    return call.sid

# --- Location Tracking and Mapping ---
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

def get_location_map(lat, lon, danger_zones, safe_zones):
    m = folium.Map(location=[lat, lon], zoom_start=6)
    for zone in danger_zones:
        folium.Marker([zone['lat'], zone['lon']], popup=f"Danger Zone: {zone['name']}", icon=folium.Icon(color='red')).add_to(m)
    for zone in safe_zones:
        folium.Marker([zone['lat'], zone['lon']], popup=f"Safe Zone: {zone['name']}", icon=folium.Icon(color='green')).add_to(m)
    return m

# --- Streamlit App ---
st.set_page_config(page_title="Women Safety App", layout="wide")

# Include the CSS directly in the code
st.markdown("""
    <style>
        /* Set a background image or color */
        .stApp {
            background: url('https://www.example.com/background-image.jpg') no-repeat center center fixed; 
            background-size: cover;
            background-color:#ccccff; /* Fallback color if image not available */
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

# Sidebar for navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Login", "Register", "Home Page", "Search Zones", "SOS", "Products"])

# --- Login Page ---
if page == "Login":
    st.markdown("<div class='main-title'>Login</div>", unsafe_allow_html=True)
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    if st.button("Login", key="login"):
        if user_exists(user_file, username):
            if authenticate_user(user_file, username, password):
                st.success("Logged in successfully!")
            else:
                st.error("Invalid username or password.")
        else:
            st.error("User not found. Please register first.")
    
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

# --- Registration Page ---
elif page == "Register":
    st.markdown("<div class='main-title'>Register</div>", unsafe_allow_html=True)
    new_username = st.text_input("New Username")
    new_password = st.text_input("New Password", type="password")
    
    if st.button("Register", key="register"):
        if new_username and new_password:
            if not user_exists(user_file, new_username):
                if add_user_to_xml(user_file, new_username, new_password):
                    st.success("Registration successful!")
                else:
                    st.error("Registration failed.")
            else:
                st.error("Username already exists. Please choose a different username.")
        else:
            st.error("Please enter both username and password.")

# --- Home Page ---
elif page == "Home Page":
    st.markdown("<div class='main-title'>Welcome to the Women Safety App</div>", unsafe_allow_html=True)

    # Slideshow
    st.markdown("""
        <div class="slideshow-container">
            <div class="mySlides">
                <img src="https://cdn.statcdn.com/Infographic/images/normal/31858.jpeg" style="width:100%">
                <div class="text">Slide 1</div>
            </div>
            <div class="mySlides">
                <img src="https://ichef.bbci.co.uk/images/ic/640x360/p099rmrv.jpg" style="width:100%">
                <div class="text">Slide 2</div>
            </div>
            <div class="mySlides">
                <img src="https://www.techugo.com/blog/wp-content/uploads/2023/09/Stay-Ahead-with-Tech-Discover-Market-Trends-in-Womens-Safety-Apps.png"  style="width:100%"> 
                <div class="text">Slide 3</div>
            </div>
            <a class="prev" onclick="plusSlides(-1)">&#10094;</a>
            <a class="next" onclick="plusSlides(1)">&#10095;</a>
        </div>
        <script>
            let slideIndex = 0;
            showSlides();
            
            function showSlides() {
                let i;
                let slides = document.getElementsByClassName("mySlides");
                for (i = 0; i < slides.length; i++) {
                    slides[i].style.display = "none";  
                }
                slideIndex++;
                if (slideIndex > slides.length) {slideIndex = 1}    
                slides[slideIndex-1].style.display = "block";  
                setTimeout(showSlides, 2000); // Change image every 2 seconds
            }
            
            function plusSlides(n) {
                showSlides(slideIndex += n);
            }
        </script>
    """, unsafe_allow_html=True)

    # Buttons on the Landing Page
    to_number = st.text_input("Enter the phone number for emergency SOS call", "+919353564074", key="sos_number_landing")
    
    if st.button("SOS Call", key="landing_sos"):
        if to_number:
            try:
                call_sid = make_call(to_number, twilio_number)
                st.success(f"Emergency SOS call initiated successfully! Call SID: {call_sid}")
            except Exception as e:
                st.error(f"Error initiating call: {e}")
        else:
            st.error("Please enter a valid phone number.")

    if st.button("SMS Alert", key="landing_sms"):
        st.success("Sending SMS alert... (Please wait)")

    if st.button("Buy Product", key="landing_buy"):
        st.success("Redirecting to product page... (Please wait)")

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
            # Default location for map (can be adjusted based on your preference)
            m = get_location_map(28.7041, 77.1025, danger_zones, safe_zones)
            st_folium(m, width=700, height=500)
        else:
            st.error(f"No data found for {district_name}")

    to_number = st.text_input("Enter the phone number for emergency SOS call", "+919353564074", key="sos_number_search")
    if st.button("SOS Call", key="search_sos"):
        if to_number:
            try:
                call_sid = make_call(to_number, twilio_number)
                st.success(f"Emergency SOS call initiated successfully! Call SID: {call_sid}")
            except Exception as e:
                st.error(f"Error initiating call: {e}")
        else:
            st.error("Please enter a valid phone number.")
           
            

# --- SOS Page ---

elif page == "SOS":
    st.markdown("<div class='main-title'>SOS Alert</div>", unsafe_allow_html=True)
    to_number = st.text_input("Enter the phone number for emergency SOS call", "+919353564074", key="sos_number_sos")
    if st.button("SOS Call", key="sos_call"):
        if to_number:
            try:
                call_sid = make_call(to_number, twilio_number)
                st.success(f"Emergency SOS call initiated successfully! Call SID: {call_sid}")
            except Exception as e:
                st.error(f"Error initiating call: {e}")
        else:
            st.error("Please enter a valid phone number.")

   
    

# --- Products Page ---
elif page == "Products":
    st.markdown("<div class='main-title'>Our Products</div>", unsafe_allow_html=True)
    
    st.markdown("<h2>Featured Products</h2>", unsafe_allow_html=True)
    st.markdown("""
        <div style="display: flex; justify-content: space-around;">
            <div style="flex: 1; padding: 10px;">
                <img src="https://img.freepik.com/premium-photo/glowing-wristband-persons-arm-illuminating-wearable-technology-enhanced-visibility-wrist-implant-measuring-various-health-parameters-ai-generated_538213-15026.jpg" alt="Product 1" style="width: 200px; height: 200px;">
                <h3>WRIST BAND</h3>
                <p></p>
            </div>
            <div style="flex: 1; padding: 10px;">
                <img src="data:image/jpeg;base64,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" alt="Product 2" style="width: 200px; height: 200px;">
                <h3>FINGER RING</h3>
                <p></p>
            </div>
            <div style="flex: 1; padding: 10px;">
                <img src="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcSvyrhwaJX5Sn__MvX3CKqYdb2e3CPBW3rBXg&s" alt="Product 3" style="width: 200px; height: 200px;">
                <h3>SMART SHOES</h3>
                <p></p>
            </div>
        </div>
    """, unsafe_allow_html=True)
# --- Footer ---
st.markdown("""
    <div class="footer">
        <p>Stay Safe! Your safety is our priority.</p>
    </div>
""", unsafe_allow_html=True)
