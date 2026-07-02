import { AuthGuard } from "@/components/AuthGuard";
import { ChapterScreen } from "@/features/soulbook/ChapterScreen";

export function generateStaticParams() {
  return [{ bookId: "_", chapterId: "_" }];
}

export const dynamicParams = false;

export default function ChapterPage() {
  return (
    <AuthGuard>
      <ChapterScreen />
    </AuthGuard>
  );
}
