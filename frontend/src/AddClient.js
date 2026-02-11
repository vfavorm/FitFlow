import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css";

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

  // ---------------- VALIDATION ----------------
  const validateForm = () => {
    const { first_name, last_name, email, phone } = formData;

    if (!first_name.trim()) {
      return "First name cannot be empty.";
    }

    if (!last_name.trim()) {
      return "Last name cannot be empty.";
    }

    // Email regex (simple + reliable)
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(email)) {
      return "Please enter a valid email address.";
    }

    // Phone: 10 digits, starts with 07 or 01
    const phoneRegex = /^(07|01)\d{8}$/;
    if (!phoneRegex.test(phone)) {
      return "Phone number must be 10 digits and start with 07 or 01.";
    }

    return null; // valid
  };
  // ------------------------------------------------

  const handleSubmit = async (e) => {
    e.preventDefault();
    setMessage("");

    const validationError = validateForm();
    if (validationError) {
      setMessage(validationError);
      return;
    }

    setLoading(true);

    try {
      const token = localStorage.getItem("access_token");

      const res = await axios.post(
        "https://fitflow-gym-prod.azurewebsites.net/addClient",
        formData,
        {
          headers: {
            Authorization: `Bearer ${token}`,
          },
        }
      );

      setMessage(res.data.message || "Client added successfully!");
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
          />

          <input
            type="text"
            name="last_name"
            placeholder="Last Name"
            value={formData.last_name}
            onChange={handleChange}
            className="input-field"
          />

          <input
            type="text"
            name="email"
            placeholder="Email"
            value={formData.email}
            onChange={handleChange}
            className="input-field"
          />

          <input
            type="tel"
            name="phone"
            placeholder="Phone Number"
            value={formData.phone}
            onChange={handleChange}
            className="input-field"
          />

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Adding..." : "Add Client"}
          </button>
        </form>

        {message && (
          <p
            className={
              message.toLowerCase().includes("success")
                ? "message-success"
                : "message-error"
            }
          >
            {message}
          </p>
        )}

        <button
          className="btn btn-secondary"
          style={{ marginTop: "1rem" }}
          onClick={() => navigate("/dashboard/admin")}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
}

export default AddClient;
