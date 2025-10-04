import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css";

function AddAdmin() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    secret_code: "", // Field for the special code
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const token = localStorage.getItem("access_token");

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");
    setError("");

    try {
      const res = await axios.post(
        "http://localhost:5000/add/admin",
        formData, // The form data now includes the secret_code
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage(res.data.message || "Admin created successfully!");
      setFormData({ name: "", email: "", password: "", secret_code: "" }); // Clear form on success
    } catch (err) {
      setError(err.response?.data?.error || err.response?.data?.message || "Please check details and try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Create New Admin</h2>
        <p>A valid secret code is required to create a new admin account.</p>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>Name:</label>
            <input type="text" name="name" value={formData.name} onChange={handleChange} className="input-field" required />
          </div>
          <div className="form-group">
            <label>Email:</label>
            <input type="email" name="email" value={formData.email} onChange={handleChange} className="input-field" required />
          </div>
          <div className="form-group">
            <label>Password:</label>
            <input type="password" name="password" value={formData.password} onChange={handleChange} className="input-field" required />
          </div>
          <div className="form-group">
            <label>Secret Code:</label>
            <input type="password" name="secret_code" placeholder="Enter the secret code" value={formData.secret_code} onChange={handleChange} className="input-field" required />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Creating..." : "Create Admin"}
          </button>
        </form>

        {message && <p className="message-success">{message}</p>}
        {error && <p className="message-error">{error}</p>}

        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => navigate("/dashboard/admin")}
          style={{ marginTop: '1rem' }}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}

export default AddAdmin;