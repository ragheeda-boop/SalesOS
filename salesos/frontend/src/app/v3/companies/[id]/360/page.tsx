import { redirect } from "next/navigation";

/** Bookmark / deep-link alias — Company 360 lives on the v3 company record. */
export default async function V3Company360AliasPage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  redirect(`/v3/companies/${id}`);
}
