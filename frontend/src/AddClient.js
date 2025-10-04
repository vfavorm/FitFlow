import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css"; // Reusing the shared Auth.css for consistent styling

function AddClient() {
  const [formData, setFormData] = useState({
    first_name: "",
    last_name: "",
    email: "",
    phone: "",
  });
  const [message, setMessage] = useState("");
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    setFormData({ ...formData, [e.target.name]: e.target.value });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const token = localStorage.getItem("access_token");
      const res = await axios.post(
        "http://localhost:5000/addClient",
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage(res.data.message || "Client added successfully!");
      // Optionally, navigate to the clients list or clear the form
      // navigate('/admin/clients'); 
      setFormData({ first_name: "", last_name: "", email: "", phone: "" });
    } catch (err) {
      setMessage(err.response?.data?.error || "Failed to add client.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Add New Client</h2>
        <form onSubmit={handleSubmit}>
          <input
            type="text"
            name="first_name"
            placeholder="First Name"
            value={formData.first_name}
            onChange={handleChange}
            className="input-field"
            required
          />
          <input
            type="text"
            name="last_name"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={handleChange}
            className="input-field"
            required
          />
          <input
            type="email"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            className="input-field"
            required
          />
          <input
            type="tel"
            name="phone"
            placeholder="Phone Number"
            value={formData.phone}
            onChange={handleChange}
            className="input-field"
            required
          />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Adding..." : "Add Client"}
          </button>
        </form>
        {message && <p className={message.toLowerCase().includes("fail") ? "message-error" : "message-success"}>{message}</p>}
        <button className="btn btn-secondary" style={{ marginTop: '1rem' }} onClick={() => navigate('/dashboard/admin')}>
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}

export default AddClient;