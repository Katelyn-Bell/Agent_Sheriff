import { DenySlamGate } from "@/components/DenySlamGate";
import { ReconnectBanner } from "@/components/ReconnectBanner";
import { Sidebar } from "@/components/Sidebar";

export default function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <>
      <div className="relative z-10 flex min-h-full flex-1 flex-col">
        <ReconnectBanner />
        <div className="flex flex-1">
          <Sidebar />
          <main className="flex-1 px-10 py-8">{children}</main>
        </div>
      </div>
      <DenySlamGate />
    </>
  );
}
