import { redirect } from "next/navigation";

/** Bookmark path — stay in v3. Employee list is the v3 surface; Emp360 stays parked. */
export default function V3EmployeeRedirectPage() {
  redirect("/v3/people");
}
