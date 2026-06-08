export function EmptyState({
  title,
  description,
}: {
  title: string;
  description?: string;
}) {
  return (
    <div className="rounded-xl border border-dashed border-zinc-800 bg-zinc-900/30 px-6 py-10 text-center">
      <p className="text-sm font-medium text-zinc-300">{title}</p>
      {description ? <p className="mt-2 text-sm text-zinc-500">{description}</p> : null}
    </div>
  );
}
