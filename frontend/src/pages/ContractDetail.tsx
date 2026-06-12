import { useEffect, useState } from 'react'
import { useParams, Link } from 'react-router-dom'
import { getContractStatus, downloadContract, type Envelope } from '../api/client'
import StatusBadge from '../components/StatusBadge'

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="flex justify-between py-3 border-b border-slate-100 last:border-0">
      <span className="text-sm text-slate-500">{label}</span>
      <span className="text-sm text-slate-800 font-medium text-right max-w-xs break-all">{value}</span>
    </div>
  )
}

function formatDate(iso: string | null) {
  if (!iso) return '—'
  return new Date(iso).toLocaleString('es-MX', {
    year: 'numeric', month: 'short', day: 'numeric',
    hour: '2-digit', minute: '2-digit',
  })
}

export default function ContractDetail() {
  const { id } = useParams<{ id: string }>()
  const [envelope, setEnvelope] = useState<Envelope | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!id) return
    getContractStatus(id)
      .then(setEnvelope)
      .catch(e => setError(e.message))
      .finally(() => setLoading(false))
  }, [id])

  return (
    <div className="max-w-xl">
      <Link to="/" className="text-sm text-slate-500 hover:text-slate-700 mb-4 inline-block">
        ← Volver al dashboard
      </Link>

      <h1 className="text-2xl font-semibold text-slate-800 mb-6">Detalle del Contrato</h1>

      {loading && <div className="text-slate-400 text-sm">Cargando…</div>}

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
          Error: {error}
        </div>
      )}

      {envelope && (
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-100 flex items-center justify-between">
            <span className="text-sm font-medium text-slate-700">
              {envelope.email_subject || '(sin asunto)'}
            </span>
            <StatusBadge status={envelope.status} />
          </div>

          <div className="px-6 py-2">
            <Row label="Envelope ID" value={envelope.envelope_id} />
            <Row label="Enviado" value={formatDate(envelope.sent_date)} />
            <Row label="Completado" value={formatDate(envelope.completed_date)} />
            {envelope.decline_reason && (
              <Row label="Motivo de rechazo" value={envelope.decline_reason} />
            )}
          </div>

          {envelope.status === 'completed' && (
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50">
              <button
                onClick={() => downloadContract(envelope.envelope_id)}
                className="w-full bg-green-600 hover:bg-green-700 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
              >
                ⬇ Descargar PDF firmado
              </button>
            </div>
          )}

          {envelope.status === 'sent' && (
            <div className="px-6 py-4 border-t border-slate-100 bg-slate-50">
              <p className="text-sm text-slate-500 text-center">
                Esperando firma del cliente…
              </p>
            </div>
          )}

          {envelope.status === 'declined' && (
            <div className="px-6 py-4 border-t border-slate-100 bg-red-50">
              <p className="text-sm text-red-600 text-center font-medium">
                El cliente rechazó el documento.
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  )
}
