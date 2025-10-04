import React from "react";
import { Link } from "react-router-dom";
import "./Auth.css"; // Reuse shared styles for consistency

function NotFound() {
  return (
    <div className="auth-container">
      <div className="auth-card">
        <img
          src="https://cdn-icons-png.flaticon.com/128/7486/7486791.png"
          alt="Not Found"
          className="auth-icon"
          style={{ padding: '20px' }}
        />
        <h2 style={{ color: '#ffc107' }}>404 - Page Not Found</h2>
        <p>
          Sorry, the page you are looking for does not exist.
        </p>
        <Link to="/" className="btn btn-primary" style={{ marginTop: '1rem' }}>
          Go to Homepage
        </Link>
      </div>
    </div>
  );
}

export default NotFound;