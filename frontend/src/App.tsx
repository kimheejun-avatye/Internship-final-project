import { Navigate, Route, Routes } from "react-router-dom";
import AuthLayout from "./layouts/AuthLayout";
import AppLayout from "./components/AppLayout";
import ProtectedRoute from "./auth/ProtectedRoute";
import LoginPage from "./pages/auth/LoginPage";
import SignupPage from "./pages/auth/SignupPage";
import PasswordResetPage from "./pages/auth/PasswordResetPage";
import ProfilePage from "./pages/profile/ProfilePage";
import ReservationPage from "./pages/reservation/ReservationPage";
import CalendarPage from "./pages/calendar/CalendarPage";
import AdminPage from "./pages/admin/AdminPage";
export default function App() {
  return <Routes>
    <Route element={<AuthLayout />}>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route path="/password/reset" element={<PasswordResetPage />} />
    </Route>
    <Route element={<ProtectedRoute />}>
      <Route element={<AppLayout />}>
        <Route path="/reservations" element={<ReservationPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/admin" element={<AdminPage />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Route>
    </Route>
    <Route path="*" element={<Navigate to="/reservations" replace />} />
  </Routes>;
}
