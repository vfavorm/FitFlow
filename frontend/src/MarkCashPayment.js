import React, { useState, useEffect } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css";
import Loader from "./Loader";

const PaymentLoggingForm = () => {
  const [formData, setFormData] = useState({
    email: "",
    subscription: "",
    payment_date: new Date().toISOString().split("T")[0],
  });

  const [clients, setClients] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isFetching, setIsFetching] = useState(true);
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  // Fetch clients & subscriptions
  useEffect(() => {
    const fetchData = async () => {
      try {
        const token = localStorage.getItem("access_token");
        
        const clientsRes = await axios.get("https://fitflow-gym-prod.azurewebsites.net/clients", {
          headers: { Authorization: `Bearer ${token}` },
        });
        const subsRes = await axios.get("https://fitflow-gym-prod.azurewebsites.net/subscriptions", {
          headers: { Authorization: `Bearer ${token}` },
        });

        const onlyClients = (clientsRes.data?.clients || []).filter(c => c.is_admin !== true);
        setClients(onlyClients);

        const subsList = Array.isArray(subsRes.data) ? subsRes.data : [];
        setSubscriptions(subsList);

        // Default subscription
        if (subsList.length > 0) {
          setFormData(prev => ({
            ...prev,
            subscription: subsList[0].name
          }));
        }

      } catch (err) {
        console.error(err);
        setMessage("Failed to load clients or subscriptions.");
      } finally {
        setIsFetching(false);
      }
    };

    fetchData();
  }, []);

  if (isFetching) return <Loader message="Loading Data..." />;

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage("");
    setErrors({});

    try {
      const token = localStorage.getItem("access_token");
      const payload = {
        email: formData.email,
        subscription: formData.subscription,
        payment_date: formData.payment_date,
      };

      const { data } = await axios.post(
        "https://fitflow-gym-prod.azurewebsites.net/markCashPayment",
        payload,
        { headers: { Authorization: `Bearer ${token}`, "Content-Type": "application/json" } }
      );

      // Backend returns accurate status and new expiry
      setMessage(
        `Payment recorded for: ${data.client}\nPlan: ${data.subscription}\nAmount: KES ${data.amount?.toFixed(2)}\nStatus: ${data.payment_status}${data.new_expiry ? `\nNew Expiry: ${data.new_expiry}` : ""}\n${data.note || ""}`
      );

    } catch (err) {
      console.error(err);
      setMessage(
        err.response?.data?.error || "Failed to record payment."
      );
      if (err.response?.data?.errors) setErrors(err.response.data.errors);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Record Payment</h2>
        <form onSubmit={handleSubmit}>

          <div className="form-group">
            <label>Client:</label>
            <select
              name="email"
              value={formData.email}
              onChange={handleChange}
              className="input-field"
              required
            >
              <option value="" disabled>Select a client...</option>
              {clients.map(c => {
                const label = `${c.first_name} ${c.last_name} (${c.email})`;
                return (
                  <option key={c.id} value={c.email}>
                    {label.length > 40 ? label.substring(0, 37) + "..." : label}
                  </option>
                );
              })}
            </select>
            {errors.email && <span className="message-error">{errors.email}</span>}
          </div>

          <div className="form-group">
            <label>Subscription Plan:</label>
            <select
              name="subscription"
              value={formData.subscription}
              onChange={handleChange}
              className="input-field"
              required
            >
              <option value="" disabled>Select a plan...</option>
              {subscriptions.map(sub => {
                const label = `${sub.name} (${sub.duration_days} days) — KES ${sub.price}`;
                return (
                  <option key={sub.id} value={sub.name}>
                    {label.length > 40 ? label.substring(0, 37) + "..." : label}
                  </option>
                );
              })}
            </select>
            {errors.subscription && <span className="message-error">{errors.subscription}</span>}
          </div>

          <div className="form-group">
            <label>Payment Date:</label>
            <input
              type="date"
              name="payment_date"
              value={formData.payment_date}
              onChange={handleChange}
              className="input-field"
              max={new Date().toISOString().split("T")[0]}
            />
          </div>

          <button type="submit" className="btn btn-primary" disabled={isLoading}>
            {isLoading ? "Processing…" : "Record Payment"}
          </button>
        </form>

        {message && <div className="message success">{message.split("\n").map((line,i) => <p key={i}>{line}</p>)}</div>}

        <button
          type="button"
          onClick={() => navigate("/dashboard/admin")}
          className="btn btn-secondary"
          style={{ marginTop: "1rem" }}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default PaymentLoggingForm;
