import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { listContracts, type Envelope } from '../api/client'
import StatusBadge from '../components/StatusBadge'

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleDateString('es-MX', {
    year: 'numeric', month: 'short', day: 'numeric',
  })
}

export default function Dashboard() {
  const [envelopes, setEnvelopes] = useState<Envelope[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    listContracts()
      .then(setEnvelopes)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div>
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-2xl font-semibold text-slate-800">Contratos</h1>
          <p className="text-sm text-slate-500 mt-0.5">Últimos 30 días</p>
        </div>
        <Link
          to="/send"
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          + Nuevo Contrato
        </Link>
      </div>

      {loading && (
        <div className="text-center py-16 text-slate-400">Cargando contratos…</div>
      )}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          Error: {error}
        </div>
      )}

      {!loading && !error && envelopes.length === 0 && (
        <div className="text-center py-16 text-slate-400">
          <p className="text-4xl mb-3">📭</p>
          <p>No hay contratos en los últimos 30 días.</p>
          <Link to="/send" className="text-blue-600 hover:underline text-sm mt-2 inline-block">
            Enviar el primero →
          </Link>
        </div>
      )}

      {!loading && envelopes.length > 0 && (
        <div className="bg-white rounded-xl border border-slate-200 overflow-hidden shadow-sm">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-slate-200 bg-slate-50">
                <th className="text-left px-4 py-3 font-medium text-slate-600">Asunto</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Estado</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Enviado</th>
                <th className="text-left px-4 py-3 font-medium text-slate-600">Completado</th>
                <th className="px-4 py-3"></th>
              </tr>
            </thead>
            <tbody>
              {envelopes.map((env, i) => (
                <tr
                  key={env.envelope_id}
                  className={`border-b border-slate-100 hover:bg-slate-50 transition-colors ${
                    i === envelopes.length - 1 ? 'border-b-0' : ''
                  }`}
                >
                  <td className="px-4 py-3">
                    <span className="text-slate-800 font-medium">
                      {env.email_subject || '(sin asunto)'}
                    </span>
                    <br />
                    <span className="text-slate-400 text-xs font-mono">{env.envelope_id}</span>
                  </td>
                  <td className="px-4 py-3">
                    <StatusBadge status={env.status} />
                  </td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(env.sent_date)}</td>
                  <td className="px-4 py-3 text-slate-600">{formatDate(env.completed_date)}</td>
                  <td className="px-4 py-3 text-right">
                    <Link
                      to={`/contracts/${env.envelope_id}`}
                      className="text-blue-600 hover:underline font-medium"
                    >
                      Ver →
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  )
}
