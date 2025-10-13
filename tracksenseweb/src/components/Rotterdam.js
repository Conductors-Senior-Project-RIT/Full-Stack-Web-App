import React from 'react';
import rotterdam from '../media/images/rotterdam.png';
import sign from '../media/images/rotterdam_sign_icon.png';
import Station from './Station';


const Rotterdam = () => {
  return (
    <Station station="Rotterdam" image={rotterdam} locationImage={sign} />
  );
};

export default Rotterdam;