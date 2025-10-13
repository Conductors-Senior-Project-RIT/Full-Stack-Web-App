import React from 'react';
import './css/AboutUs.css';
import eot_video from '../media/videos/eot_video.mp4';
import eot_image from '../media/images/eot_image.png';

const AboutUs = () => {
    return (
        <div class="container">
        <section>
            <h2>Meet the Sponsor</h2>
            <p>Ken Gentzke Jr</p>
            <p>My grandfather worked for the Erie Lackawanna RR. He always took me to the yard for rides
                in the yard or on local trains to serve customers on the line. Since then I always enjoy watching trains go by which keeps memories of my grandfather alive.
                My inspiration for this project is to be able to know where the trains are, just the same way with other people and their radios. This will help to overcome the communication barrier for the deaf railfans. I hope this will become successful with the railfan community, especially for other deaf railfans. I'm planning on to expanding out to other states. </p>
        </section>
        
        <section>
            <h2>What is Follow That FRED?</h2>
            <p>Follow That FRED provides an easy way for railfans to view the telemetry data collected from passing trains at each location, as well as view the times when trains passed by each location throughout the day. In addition, users can sign up for a messaging service, Pushover, to receive alerts from select locations when a train is detected nearby. The historical data page provides options for filtering and searching through all of the data collected, whether by dates or any category of information transmitted through EOT or HOT telemetry. </p>
        </section>

        <section>
            <h2>Features</h2>
            <h3>Real-Time Tracking</h3>
            <p>Follow That FRED! provides real-time tracking of trains. Users can monitor train movements with precision, ensuring they are always up-to-date with the latest information.</p>

            <h3>Historical Data</h3>
            <p>The platform archives extensive records of past train activity, allowing users to access and review historical data. This feature is ideal for enthusiasts who wish to study train patterns and schedules over time.</p>

            <h3>Accessibility for Deaf Enthusiasts</h3>
            <p>Recognizing the challenges faced by deaf rail enthusiasts, Follow That FRED! includes visual means of engagement. The platform also features a notification system to alert users when trains are approaching their vicinity, ensuring they can make the most of their viewing opportunities.</p>
        </section>

        <section>
            <h2>EOT Device Examples</h2>
            <img src={eot_image} alt="End Of Train Device" className="image-class" />
            <video controls className="video-class">
            <source src={eot_video} type="video/mp4" />
            Your browser does not support the video tag.
            </video>
        </section>

    </div>
    );
};

export default AboutUs;