import React from "react";
import { BrowserRouter as Router, Routes, Route } from "react-router-dom";
import "./shared.css"; // Import shared styles
import ClientLogin from "./ClientLogin";
import ClientDashboard from "./ClientDashboard";
import AdminDashboard from "./AdminDashboard";
import Home from "./Home";
import AdminLogin from "./AdminLogin";
import AddClient from "./AddClient";
import AddExpense from "./AddExpense";
import ExpenseList from "./AllExpenses";
import ProtectedRoute from './ProtectedRoutes';
import ClientsList from "./ViewClients";
import PaymentLoggingForm from "./MarkCashPayment";
import MpesaPayment from "./Payment";
import ClientUpdate from "./UpdateProfile";
import PaymentsList from "./PaymentList";
import AddAdmin from "./AddAdmin";
import AdminUpdate from "./UpdateAdmin"; // create this component
import ForgotPassword from "./ForgotPassword";
import ResetPassword from "./ResetPassword";
import NotFound from "./NotFound";
import Invoices from './Invoices';


function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/client/login" element={<ClientLogin />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password" element={<ResetPassword />} />
        <Route path="/admin/create" element={<AddAdmin />} />



        {/* Protected routes */}
        <Route path="/dashboard/admin" element={
          <ProtectedRoute redirectTo="/admin/login">
            <AdminDashboard />
          </ProtectedRoute>
        } />
        <Route path="/addClient" element={
          <ProtectedRoute redirectTo="/admin/login">
            <AddClient />
          </ProtectedRoute>
        } />

        <Route path="/dashboard/client" element={
          <ProtectedRoute redirectTo="/client/login">
            <ClientDashboard />
          </ProtectedRoute>
        } />

        <Route path="/client/invoices" element={
          <ProtectedRoute redirectTo="/client/login">
            <Invoices />
          </ProtectedRoute>
        } />

        <Route path="/addExpense" element={
          <ProtectedRoute redirectTo="/admin/login">
            <AddExpense />
          </ProtectedRoute>
        } />
        <Route path="/expenses"  element={
          <ProtectedRoute redirectTo="/admin/login">
            <ExpenseList />
          </ProtectedRoute>
        } />
        <Route path="/clients"  element={
          <ProtectedRoute redirectTo="/admin/login">
            <ClientsList />
          </ProtectedRoute>
        } />
        <Route path="/markCashPayment"  element={
          <ProtectedRoute redirectTo="/admin/login">
            <PaymentLoggingForm />
          </ProtectedRoute>
        } />
        <Route path="/payment"  element={
          <ProtectedRoute redirectTo="/client/login">
            <MpesaPayment />
          </ProtectedRoute>
        } />
        <Route path="/update"  element={
          <ProtectedRoute redirectTo="/client/login">
            <ClientUpdate />
          </ProtectedRoute>
        } />
        <Route path="/payments"  element={
          <ProtectedRoute redirectTo="/client/login">
            <PaymentsList />
          </ProtectedRoute>
        } />

        <Route path="/admin/update" element={
          <ProtectedRoute redirectTo="/admin/login">
            <AdminUpdate />
          </ProtectedRoute>
        } />

        {/* Catch-all 404 Route */}
        <Route path="*" element={<NotFound />} />

      </Routes>
    </Router>
  );
}

export default App;
