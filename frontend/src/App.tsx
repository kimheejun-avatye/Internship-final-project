import { Navigate, Route, Routes } from "react-router-dom";

import AppLayout from "./components/AppLayout";
import AdminPage from "./pages/admin/AdminPage";
import LoginPage from "./pages/auth/LoginPage";
import SignupPage from "./pages/auth/SignupPage";
import CalendarPage from "./pages/calendar/CalendarPage";
import ReservationPage from "./pages/reservation/ReservationPage";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/signup" element={<SignupPage />} />
      <Route element={<AppLayout />}>
        <Route path="/reservations" element={<ReservationPage />} />
        <Route path="/calendar" element={<CalendarPage />} />
        <Route path="/admin" element={<AdminPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/login" replace />} />
    </Routes>
  );
}
