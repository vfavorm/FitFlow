import React from 'react';
import './Loader.css';

const Loader = ({ message = "Loading..." }) => {
  return (
    <div className="loader-overlay">
      <div className="spinner"></div>
      <h3>{message}</h3>
      <p>Please wait while we prepare your data.</p>
    </div>
  );
};

export default Loader;