import React from 'react';
import solvay from '../media/images/solvay.png';
import sign from '../media/images/solvay_sign_icon.png';
import Station from './Station'


const Solvay = () => {
  return (
    <Station station="Solvay" image={solvay} locationImage={sign} />
  );
};

export default Solvay;