export default function MarketingLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="relative z-10 flex min-h-full flex-1 flex-col">
      {children}
    </div>
  );
}
