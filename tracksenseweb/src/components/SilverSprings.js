import React from 'react';
import silver_springs from '../media/images/silver_springs.png';
import sign from '../media/images/silver_springs_sign_icon.png';
import Station from './Station';


const SilverSprings = () => {
  return (
    <Station station="Silver Springs" image={silver_springs} locationImage={sign}></Station>
  );
};

export default SilverSprings;