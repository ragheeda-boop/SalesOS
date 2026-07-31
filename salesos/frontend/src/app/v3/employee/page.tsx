import { redirect } from "next/navigation";

/** Legacy / bookmark path — Emp360 lives under /employees/me */
export default function V3EmployeeRedirectPage() {
  redirect("/employees/me");
}
