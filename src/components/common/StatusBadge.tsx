export default function StatusBadge({
  children = "DEMO MODE",
}: {
  children?: string;
}) {
  return (
    <span className="status-badge">
      <i />
      {children}
    </span>
  );
}
