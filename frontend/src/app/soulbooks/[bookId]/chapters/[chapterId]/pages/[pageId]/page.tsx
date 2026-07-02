import { AuthGuard } from "@/components/AuthGuard";
import { WritingPage } from "@/features/soulbook/WritingPage";

export function generateStaticParams() {
  return [{ bookId: "_", chapterId: "_", pageId: "_" }];
}

export const dynamicParams = false;

export default function WritingRoutePage() {
  return (
    <AuthGuard>
      <WritingPage />
    </AuthGuard>
  );
}
