import React, { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  FaUserPlus,
  FaMoneyBill,
  FaCashRegister,
  FaUsers,
  FaReceipt,
  FaUserCog,
} from "react-icons/fa";
import { FiMoreVertical } from "react-icons/fi"; // three dots icon
import "./AdminDashboard.css";
import Loader from "./Loader";

function AdminDashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState({
    clients: 0,
    expenses: 0,
    payments: 0,
  });

  const [subscriptions, setSubscriptions] = useState([]); // store subscription list
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchData = async () => {
      const token = localStorage.getItem("access_token");
      
      try {
        const [statsRes, subsRes] = await Promise.all([
          fetch("https://fitflow-gym-prod.azurewebsites.net//dashboard", {
            headers: {
              "Content-Type": "application/json",
              "Authorization": `Bearer ${token}`
            }
          }),
          fetch("https://fitflow-gym-prod.azurewebsites.net//subscriptions")
        ]);

        if (statsRes.ok) setStats(await statsRes.json());
        if (subsRes.ok) setSubscriptions(await subsRes.json());

      } catch (err) {
        console.error("Error fetching dashboard data:", err);
      } finally {
        setLoading(false);
      }
    };
    fetchData();
  }, []);

  const actions = [
    { label: "Add Client", icon: <FaUserPlus />, route: "/addClient" },
    { label: "Add Expense", icon: <FaMoneyBill />, route: "/addExpense" },
    { label: "Mark Cash Payment", icon: <FaCashRegister />, route: "/markCashPayment" },
    { label: "Client List", icon: <FaUsers />, route: "/clients" },
    { label: "Expenses", icon: <FaReceipt />, route: "/expenses" },
    { label: "Update Profile", icon: <FaUserCog />, route: "/admin/update" },
  ];

  if (loading) return <Loader message="Loading Dashboard..." />;

  return (
    <div className="dashboard-wrapper">
      <div className="dashboard-card-bg">
        {/* Header with actions button */}
        <div className="dashboard-header">
          <h1 className="dashboard-title">Admin Dashboard</h1>
          <div className="actions-menu">
            <button
              className="actions-toggle"
              onClick={() => setDropdownOpen(!dropdownOpen)}
            >
              <FiMoreVertical size={22} />
            </button>
            {dropdownOpen && (
              <ul className="actions-dropdown">
                {actions.map((action, idx) => (
                  <li
                    key={idx}
                    className="dropdown-item"
                    onClick={() => navigate(action.route)}
                  >
                    <span className="dropdown-icon">{action.icon}</span>
                    <span>{action.label}</span>
                  </li>
                ))}
              </ul>
            )}
          </div>
        </div>

        {/* Admin details */}
        <div className="admin-details">
          <h2>Welcome Back</h2>
        </div>

        {/* Stats Section */}
        <div className="stats-container">
          <div className="stat-box">
            <h3>Total Clients</h3>
            <div className="stat-amount">{stats.clients}</div>
          </div>
          <div className="stat-box">
            <h3>Expenses</h3>
            <div className="stat-amount">{stats.expenses}</div>
          </div>
          <div className="stat-box">
            <h3>Payments</h3>
            <div className="stat-amount">{stats.payments}</div>
          </div>
        </div>

        {/* Subscriptions Section */}
        <div className="subscriptions-section">
          <h2>Subscriptions</h2>
          {subscriptions.length > 0 ? (
            <ul className="subscription-list">
              {subscriptions.map((sub) => (
                <li key={sub.id} className="subscription-item">
                  <div className="sub-name">{sub.name}</div>
                  <div className="sub-price">Ksh. {sub.price}</div>
                  <div className="sub-duration">{sub.duration_days} days</div>
                </li>
              ))}
            </ul>
          ) : (
            <p>No subscriptions found.</p>
          )}
        </div>
      </div>
    </div>
  );
}

export default AdminDashboard;
