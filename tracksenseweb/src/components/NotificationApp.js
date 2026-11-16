import React from 'react';
import './css/AboutUs.css';
import step1 from "./../media/images/notification-system/STEP1.PNG";
import step2 from "./../media/images/notification-system/STEP2.JPEG";
import step3 from "./../media/images/notification-system/STEP3.PNG";
import step4 from "./../media/images/notification-system/STEP4.PNG";

const NotificationApp = () => {
    return (
        <div class="container">
        <section>
            <h2>How to Set Up The Notification App</h2>
            <p>Step 1. Download the app "Ntfy". It is available on iOS and Android.</p>
            <img src={step1} style={{ width: "300px" }}/>
            <br/>
            <br/>
            <br/>
            <br/>
            <p>Step 2. In the app, click the + icon on top right corner.</p>
            <img src={step2} style={{ width: "300px" }}/>
            <br/>
            <br/>
            <br/>
            <br/>
            <p>3. For the subject topic, put the station name that you want to receive notifications about.</p>
            <p>Enable "use another server" option and put "http://tracksense.se.rit.edu:6161" for the custom server.</p>
            <img src={step3} style={{ width: "300px" }}/>
            <br/>
            <br/>
            <br/>
            <br/>
            <p>You now should be able to see past notifications and receive new ones when they are pushed out.</p>
            <img src={step4} style={{ width: "300px" }}/>
        </section>

    </div>
    );
};

export default NotificationApp;