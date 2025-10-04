import React, { useState, useEffect } from "react";
import { useSearchParams, useNavigate, Link } from "react-router-dom";
import axios from "axios";
import "./Auth.css";

function ResetPassword() {
  const [searchParams] = useSearchParams();
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const token = searchParams.get("token");

  useEffect(() => {
    if (!token) {
      setError("No reset token found. Please use the link from your email.");
    }
  }, [token]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");
    setError("");

    if (password !== confirmPassword) {
      setError("Passwords do not match.");
      return;
    }
    if (password.length < 6) {
      setError("Password must be at least 6 characters long.");
      return;
    }

    setLoading(true);
    try {
      const res = await axios.post(
        "http://localhost:5000/reset-password",
        { new_password: password },
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage(res.data.message);
      setTimeout(() => navigate("/client/login"), 3000); // Redirect to login after success
    } catch (err) {
      setError(err.response?.data?.message || err.response?.data?.error || "Failed to reset password. The link may have expired.");
    } finally {
      setLoading(false);
    }
  };

  if (message) {
    return (
      <div className="auth-container">
        <div className="auth-card">
          <h2>Password Reset Successful</h2>
          <p className="message-success">{message}</p>
          <Link to="/client/login" className="btn btn-primary">Proceed to Login</Link>
        </div>
      </div>
    );
  }

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Set a New Password</h2>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="new-password">New Password</label>
            <input id="new-password" type="password" placeholder="Enter your new password" value={password} onChange={(e) => setPassword(e.target.value)} className="input-field" required />
          </div>
          <div className="form-group">
            <label htmlFor="confirm-password">Confirm New Password</label>
            <input id="confirm-password" type="password" placeholder="Confirm your new password" value={confirmPassword} onChange={(e) => setConfirmPassword(e.target.value)} className="input-field" required />
          </div>
          <button type="submit" className="btn btn-primary" disabled={loading || !token}>
            {loading ? "Resetting..." : "Reset Password"}
          </button>
        </form>
        {error && <p className="message-error">{error}</p>}
      </div>
    </div>
  );
}

export default ResetPassword;