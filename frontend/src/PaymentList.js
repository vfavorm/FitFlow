import React, { useEffect, useState } from "react";
import axios from "axios"; // Use axios for consistency
import "./PaymentList.css"; // Use new stylesheet
import { useNavigate } from "react-router-dom";
import Loader from "./Loader";

function PaymentsList() {
  const [payments, setPayments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null); // Add error state
  const navigate = useNavigate();
  

  useEffect(() => {
    const token = localStorage.getItem("access_token");

    const fetchPayments = async () => {
      try {
        const res = await axios.get("https://fitflow-gym-prod.azurewebsites.net//client/payments", {
          headers: { Authorization: `Bearer ${token}` },
        });
        setPayments(res.data);
      } catch (err) {
        setError(err.response?.data?.error || "Failed to fetch payment history.");
        console.error("Error fetching payments:", err);
      } finally {
        setLoading(false);
      }
    };

    fetchPayments();
  }, []);

  if (loading) {
    return <Loader message="Loading payments..." />;
  }

  return (
    <div className="payments-page-container">
      <div className="payments-card">
        <div className="payments-header">
          <h2>Payment History</h2>
          <button className="btn btn-secondary" onClick={() => navigate('/dashboard/client')}>
            Back to Dashboard
          </button>
        </div>

        {error && (
          <div className="message-error" style={{ textAlign: 'center' }}>
            {error}
          </div>
        )}

        <div className="payments-table-container">
          <table className="payments-table">
            <thead>
              <tr>
                <th>Payment ID</th>
                <th>Amount</th>
                <th>Date</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {payments.length > 0 ? (
                payments.map((p) => (
                  <tr key={p.id}>
                    <td>{p.id}</td>
                    <td>KES {p.amount.toLocaleString()}</td>
                    <td>{new Date(p.created_at).toLocaleDateString()}</td>
                    <td>
                      <span className={`status-badge ${p.status?.toLowerCase()}`}>
                        {p.status}
                      </span>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="4" className="no-payments">No payments have been made yet.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

export default PaymentsList;
