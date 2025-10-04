// ProtectedRoute.js
import { Navigate } from "react-router-dom";

const ProtectedRoute = ({ children, redirectTo = "/client/login" }) => {
  const token = localStorage.getItem("access_token");
  
  if (!token) {
    return <Navigate to={redirectTo} replace />;
  }
  
  return children;
};

export default ProtectedRoute;