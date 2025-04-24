import { WordPressManager } from "@/components/WordPressManager";

export default function Home() {
  return (
    <main className="container mx-auto py-8">
      <h1 className="text-3xl font-bold mb-8">AutoPinner Dashboard</h1>
      <div className="grid gap-8">
        <WordPressManager />
      </div>
    </main>
  );
} 