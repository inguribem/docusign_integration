const STYLES: Record<string, string> = {
  sent: 'bg-blue-100 text-blue-700',
  delivered: 'bg-indigo-100 text-indigo-700',
  completed: 'bg-green-100 text-green-700',
  declined: 'bg-red-100 text-red-700',
  voided: 'bg-slate-100 text-slate-600',
  created: 'bg-yellow-100 text-yellow-700',
}

export default function StatusBadge({ status }: { status: string }) {
  const cls = STYLES[status] ?? 'bg-slate-100 text-slate-600'
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${cls}`}>
      {status}
    </span>
  )
}
