import { AuthGuard } from "@/components/AuthGuard";
import { BookScreen } from "@/features/soulbook/BookScreen";

// Static export placeholder: real ids are read from the live URL at runtime and
// served via the FastAPI SPA fallback. See app/spa.py.
export function generateStaticParams() {
  return [{ bookId: "_" }];
}

export const dynamicParams = false;

export default function BookPage() {
  return (
    <AuthGuard>
      <BookScreen />
    </AuthGuard>
  );
}
