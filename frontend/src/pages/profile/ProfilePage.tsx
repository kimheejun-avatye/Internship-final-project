import { useAuth } from "../../auth/AuthProvider";
import PasswordChangeForm from "./PasswordChangeForm";
export default function ProfilePage() {
  const { session } = useAuth();
  return <><h1>비밀번호 변경</h1><p className="notice">{session?.user.email}</p><PasswordChangeForm /></>;
}
