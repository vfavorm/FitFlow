import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css"; // Use the shared Auth.css for styling

function UpdateAdmin() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    old_password: "",
    new_password: "",
  });
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isFetching, setIsFetching] = useState(true);
  const navigate = useNavigate();

  const token = localStorage.getItem("access_token");

  useEffect(() => {
    const fetchAdminDetails = async () => {
      if (!token) {
        navigate("/admin/login");
        return;
      }
      try {
        setIsFetching(true);
        // This endpoint assumes you have a way to get current admin details.
        // If not, you might need to create a '/admin/details' endpoint.
        const res = await axios.get("http://localhost:5000/admin/details", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setFormData((prev) => ({
          ...prev,
          name: res.data.admin.name,
          email: res.data.admin.email,
        }));
      } catch (err) {
        setMessage("Failed to load admin details.");
        console.error(err);
      } finally {
        setIsFetching(false);
      }
    };
    fetchAdminDetails();
  }, [token, navigate]);

  const handleChange = (e) => {
    setFormData((prevFormData) => ({
      ...prevFormData,
      [e.target.name]: e.target.value,
    }));
  };

  const handleUpdate = async (e) => {
    e.preventDefault();
    setLoading(true);
    setMessage("");

    try {
      const res = await axios.put(
        "http://localhost:5000/admin/update",
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage(res.data.message || "Profile updated successfully!");
      // Clear password fields after submission
      setFormData(prev => ({ ...prev, old_password: "", new_password: "" }));
    } catch (err) {
      setMessage(err.response?.data?.message || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  if (isFetching) return <div className="loading">Loading profile...</div>;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Update Admin Profile</h2>
        <form onSubmit={handleUpdate}>
          <div className="form-group">
            <label>Name:</label>
            <input type="text" name="name" value={formData.name} onChange={handleChange} className="input-field" />
          </div>
          <div className="form-group">
            <label>Email:</label>
            <input type="email" name="email" value={formData.email} onChange={handleChange} className="input-field" />
          </div>
          <div className="form-group">
            <label>Old Password:</label>
            <input type="password" name="old_password" placeholder="Enter old password to change" value={formData.old_password} onChange={handleChange} className="input-field" />
          </div>
          <div className="form-group">
            <label>New Password:</label>
            <input type="password" name="new_password" placeholder="Enter new password" value={formData.new_password} onChange={handleChange} className="input-field" />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Updating..." : "Update Profile"}
          </button>
        </form>

        {message && (
          <p className={message.toLowerCase().includes("fail") || message.toLowerCase().includes("incorrect") ? "message-error" : "message-success"}>
            {message}
          </p>
        )}

        <button
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

export default UpdateAdmin;
