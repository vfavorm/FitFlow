import React, { useState } from "react";
import axios from "axios";
import { useNavigate } from "react-router-dom";
import "./Auth.css"; // Using shared Auth.css for consistent styling

function AddExpense() {
  const [formData, setFormData] = useState({
    expense: "",
    cost: "",
  });
  const [message, setMessage] = useState("");
  const [errors, setErrors] = useState({});
  const [loading, setLoading] = useState(false);
  const navigate = useNavigate();

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
  };

  const validateForm = () => {
    const newErrors = {};
    if (!formData.expense) newErrors.expense = "Expense description is required";
    if (!formData.cost) {
      newErrors.cost = "Cost is required";
    } else if (isNaN(formData.cost) || parseFloat(formData.cost) <= 0) {
      newErrors.cost = "Please enter a valid positive number";
    }
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) {
      return;
    }
    setLoading(true);
    setMessage("");

    try {
      const token = localStorage.getItem("access_token");
      const res = await axios.post(
        "https://fitflow-1-aqnu.onrender.com/addExpense",
        formData,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      setMessage(res.data.message || "Expense added successfully!");
      setFormData({ expense: "", cost: "" }); // Clear form
    } catch (err) {
      setMessage(err.response?.data?.error || "Failed to add expense.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Add New Expense</h2>
        <form onSubmit={handleSubmit}>
          <input
            name="expense"
            type="text"
            placeholder="Expense Description"
            value={formData.expense}
            onChange={handleChange}
            className="input-field"
            required
          />
          {errors.expense && <p className="message-error">{errors.expense}</p>}
          <input
            name="cost"
            type="number"
            placeholder="Cost (KES)"
            value={formData.cost}
            onChange={handleChange}
            className="input-field"
            min="0"
            step="0.01"
            required
          />
          {errors.cost && <p className="message-error">{errors.cost}</p>}
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? "Adding..." : "Add Expense"}
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

export default AddExpense;