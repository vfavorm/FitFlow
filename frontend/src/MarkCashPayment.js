import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { useNavigate } from 'react-router-dom';
import "./Auth.css"; // Using shared Auth.css for consistent styling

const PaymentLoggingForm = () => {
  const [formData, setFormData] = useState({
    email: '',
    subscription: '',
    payment_status: 'success',
    amount: '',
    payment_date: new Date().toISOString().split('T')[0],
  });

  const [clients, setClients] = useState([]);
  const [subscriptions, setSubscriptions] = useState([]);
  const [filteredSubscriptions, setFilteredSubscriptions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [message, setMessage] = useState('');
  const [balanceInfo, setBalanceInfo] = useState('');
  const [errors, setErrors] = useState({});
  const navigate = useNavigate();

  useEffect(() => {
    const fetchData = async () => {
      try {
        setIsLoading(true);
        const token = localStorage.getItem('access_token');

        const clientsRes = await axios.get('http://localhost:5000/clients', { headers: { Authorization: `Bearer ${token}` } });
        const subsRes = await axios.get('http://localhost:5000/subscriptions', { headers: { Authorization: `Bearer ${token}` } });

        const clientsList = clientsRes.data?.clients || [];
        const subsList = Array.isArray(subsRes.data) ? subsRes.data : [];

        setClients(clientsList);
        setSubscriptions(subsList);
        setFilteredSubscriptions(subsList);
        // --- FIX: Set a default subscription ---
        if (subsList.length > 0) {
          setFormData(prev => ({
            ...prev,
            subscription: subsList[0].name,
          }));
        }
      } catch (error) {
        console.error('Error fetching data:', error);
        setMessage('Failed to load data');
      } finally {
        setIsLoading(false);
      }
    };

    fetchData();
  }, []);

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    if (name === 'email') {
      const selectedClient = clients.find(c => c.email === value);
      if (selectedClient) {
        fetchClientBalance(selectedClient.id);
        // Filter out the plan the client already has
        if (selectedClient.subscription) {
          setFilteredSubscriptions(subscriptions);
        }
      } else {
        setBalanceInfo('');
        setFilteredSubscriptions(subscriptions);
      }
    }
  };

  const fetchClientBalance = async (clientId) => {
    try {
      const token = localStorage.getItem('access_token');
      const res = await axios.get(`http://localhost:5000/client/${clientId}/balance`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      const balance = res.data.account_balance;
      if (balance < 0) {
        setBalanceInfo(`This client has an outstanding debt of KES ${Math.abs(balance).toFixed(2)}.`);
      } else if (balance > 0) {
        setBalanceInfo(`This client has a credit of KES ${balance.toFixed(2)}.`);
      } else {
        setBalanceInfo(''); // Clear info if balance is zero or not applicable
      }
    } catch (err) { console.error("Failed to fetch balance", err); }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setIsLoading(true);
    setMessage('');
    setErrors({});

    try {
      const token = localStorage.getItem('access_token');
      const payload = {
        email: formData.email,
        subscription: formData.subscription,
        payment_status: formData.payment_status,
        amount: formData.amount ? Number(formData.amount) : null,
        payment_date: formData.payment_date,
      };

      const { data } = await axios.post('http://localhost:5000/markCashPayment', payload, {
        headers: { Authorization: `Bearer ${token}`, 'Content-Type': 'application/json' },
      });

      // Handle different success messages for subscription vs. debt payment
      if (data.new_balance !== undefined) {
        setMessage(`Debt payment of KES ${data.amount_paid.toFixed(2)} recorded for ${data.client}. New balance is KES ${data.new_balance.toFixed(2)}.`);
      } else {
        setMessage(
          [
            `Payment processed for: ${data.client}`,
            `Plan: ${data.subscription}`,
            `Status: ${data.payment_status}`,
            data.new_expiry ? `New expiry: ${data.new_expiry}` : null,
            data.note ? data.note : null,
            data.credit ? `Credit Balance: KES ${data.credit.toFixed(2)}` : null,
          ].filter(Boolean).join('\n')
        );
      }
    } catch (error) {
      console.error('Payment logging failed:', error);
      setMessage(
        error.response?.data?.error ||
        error.response?.data?.message ||
        'Payment logging failed'
      );
      if (error.response?.data?.errors) setErrors(error.response.data.errors);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="auth-container">
      <div className="auth-card">
        <h2>Record Manual Payment</h2>

        <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Client Email:</label>
          <input
            list="client-emails"
            name="email"
            value={formData.email}
            className="input-field"
            onChange={handleChange}
            required
          />
          <datalist id="client-emails">
            {clients.map(c => (
              <option key={c.id} value={c.email}>{`${c.first_name} ${c.last_name} (${c.email})`}</option>
            ))}
          </datalist>
          {balanceInfo && <p className="balance-info">{balanceInfo}</p>}
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
            <option value="" disabled>
              Select a plan...
            </option>

            {filteredSubscriptions.map(sub => (
              <option key={sub.id} value={sub.name}>
                {sub.name} ({sub.duration_days} days) — KES {sub.price}
              </option>
            ))}
          </select>
          {errors.subscription && <span className="message-error">{errors.subscription}</span>}
        </div>

        <div className="form-group">
          <label>Payment Status:</label>
          <select
            name="payment_status"
            value={formData.payment_status}
            onChange={handleChange}
            className="input-field"
            required
          >
            <option value="success">success</option>
            <option value="pending">pending</option>
            <option value="failed">failed</option>
          </select>
        </div>

        <div className="form-group">
          <label>Amount Paid:</label>
          <input
            type="number"
            name="amount"
            value={formData.amount}
            onChange={handleChange}
            className="input-field"
            placeholder="Leave empty to use plan price"
            min="3000"
            step="1000"
          />
        </div>

        <div className="form-group">
          <label>Payment Date:</label>
          <input
            type="date"
            name="payment_date"
            value={formData.payment_date}
            onChange={handleChange}
            className="input-field"
            max={new Date().toISOString().split('T')[0]}
          />
        </div>

        <button type="submit" className="btn btn-primary" disabled={isLoading}>
          {isLoading ? 'Processing…' : 'Record Payment'}
        </button>

      </form>

      {message && (
        <div className={`message ${message.toLowerCase().includes('fail') ? 'error' : 'success'}`}>
          {message.split('\n').map((line, i) => <p key={i} className={message.toLowerCase().includes('fail') ? 'message-error' : 'message-success'}>{line}</p>)}
        </div>
      )}

        <button
          type="button"
          onClick={() => navigate('/dashboard/admin')}
          className="btn btn-secondary"
          style={{ marginTop: '1rem' }}
        >
          Back to Dashboard
        </button>
      </div>
    </div>
  );
};

export default PaymentLoggingForm;
