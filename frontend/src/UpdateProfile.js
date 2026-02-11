import React, { useEffect, useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css"; // Use the shared Auth.css for styling
import Loader from "./Loader";

const ClientUpdate = () => {
  const [client, setClient] = useState(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [isFetching, setIsFetching] = useState(true);

  const token = localStorage.getItem("access_token");
  const navigate = useNavigate();

  // Fetch current client details
  useEffect(() => {
    const fetchClient = async () => {
      try {
        setIsFetching(true);
        const res = await axios.get("https://fitflow-gym-prod.azurewebsites.net/dashboard/client", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setClient(res.data.client);
      } catch (err) {
        console.error("Failed to fetch client details", err);
        setMessage("Failed to load your profile. Please try again later.");
      } finally {
        setIsFetching(false);
      }
    };
    fetchClient();
  }, [token]);

  const handleUpdate = async (e) => {
    e.preventDefault();
    if (!client) return;

    setLoading(true);
    setMessage("");

    try {
      const res = await axios.patch(
        `https://fitflow-gym-prod.azurewebsites.net/clients/${client.id}`,
        {
          first_name: client.first_name,
          last_name: client.last_name,
          email: client.email,
          phone: client.phone,
        },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      setMessage(res.data.message || "Profile updated successfully.");
    } catch (err) {
      setMessage(err.response?.data?.error || "Failed to update profile.");
    } finally {
      setLoading(false);
    }
  };

  if (isFetching) return <Loader message="Loading profile..." />;
  if (!client && !isFetching) return <div className="error">{message || "Could not load client profile."}</div>;

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Update Your Details</h2>

        <form onSubmit={handleUpdate}>
          <div className="form-group">
            <label>First Name:</label>
            <input
              type="text"
              value={client.first_name}
              className="input-field"
              onChange={(e) =>
                setClient({ ...client, first_name: e.target.value })
              }
            />
          </div>

          <div className="form-group">
            <label>Last Name:</label>
            <input
              type="text"
              value={client.last_name}
              className="input-field"
              onChange={(e) =>
                setClient({ ...client, last_name: e.target.value })
              }
            />
          </div>

          <div className="form-group">
            <label>Email:</label>
            <input
              type="email"
              value={client.email}
              className="input-field"
              onChange={(e) => setClient({ ...client, email: e.target.value })}
            />
          </div>

          <div className="form-group">
            <label>Phone:</label>
            <input
              type="tel"
              value={client.phone}
              className="input-field"
              onChange={(e) => setClient({ ...client, phone: e.target.value })}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Updating..." : "Update Profile"}
          </button>
        </form>

        {message && <p className={message.toLowerCase().includes("fail") ? "message-error" : "message-success"}>{message}</p>}
        <button
          type="button"
          className="btn btn-secondary"
          onClick={() => navigate('/dashboard/client')}
          style={{ marginTop: '1rem' }}>
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default ClientUpdate;
