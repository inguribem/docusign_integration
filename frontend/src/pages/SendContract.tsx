import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { sendContract, previewContract, getContractDefaults } from '../api/client'
import type { NDAFields, MSAFields, SOWFields, SupportSOWFields, AcceptanceFields, GenNDAFields, GenMSAFields, ContractDefaults } from '../api/client'

const CONTRACT_TYPES = ['nda', 'msa', 'sow', 'invoice_sow', 'support', 'acceptance', 'gen_nda', 'gen_msa']

const CONTRACT_TYPE_LABELS: Record<string, string> = {
  nda:         'NDA',
  msa:         'MSA',
  sow:         'SOW (App Dev)',
  invoice_sow: 'SOW (Invoice Automation)',
  support:     'SOW (Support & Maintenance)',
  acceptance:  'Acceptance Certificate',
  gen_nda:     'NDA (Generated PDF)',
  gen_msa:     'MSA (Generated PDF)',
}
const MONTHS = ['January','February','March','April','May','June',
                 'July','August','September','October','November','December']

const today = new Date()

// Campos comunes del cliente (aplican a todos los tipos de contrato)
interface ClientInfo {
  client_name: string
  client_email: string
  client_entity_type: string
  client_signer_name: string
  client_title: string
  client_address: string
}

// Términos comerciales NDA (sin los campos de cliente)
interface NDATerms {
  effective_day: string
  effective_month: string
  effective_year: string
  agreement_term: string
  non_solicitation_term: string
  governing_county: string
}

// Términos comerciales MSA (sin los campos de cliente)
interface MSATerms {
  effective_day: string
  effective_month: string
  effective_year: string
  payment_terms: string
  late_fee_rate: string
  agreement_term: string
  non_solicitation_term: string
  governing_county: string
}

const DEFAULT_CLIENT: ClientInfo = {
  client_name: '',
  client_email: '',
  client_entity_type: 'Individual',
  client_signer_name: '',
  client_title: '',
  client_address: '',
}

const DEFAULT_NDA_TERMS: NDATerms = {
  effective_day: String(today.getDate()),
  effective_month: MONTHS[today.getMonth()],
  effective_year: String(today.getFullYear()),
  agreement_term: '2 years',
  non_solicitation_term: '1 year',
  governing_county: 'Miami-Dade',
}

const DEFAULT_MSA_TERMS: MSATerms = {
  effective_day: String(today.getDate()),
  effective_month: MONTHS[today.getMonth()],
  effective_year: String(today.getFullYear()),
  payment_terms: '15',
  late_fee_rate: '1.5',
  agreement_term: '1 year',
  non_solicitation_term: '1 year',
  governing_county: 'Miami-Dade',
}

// Milestones fijos del AppDev SOW (solo duración y pago son variables)
const SOW_MILESTONE_NAMES = [
  'Discovery & Design',
  'Landing Page & Booking',
  'WhatsApp API & Tracking Automation',
  'Management WebApp',
  'QA, Testing & Launch',
]

// Milestones fijos del SOW de Automatización de Facturas (solo duración y pago son variables)
const INVOICE_SOW_MILESTONE_NAMES = [
  'Discovery & Solution Design',
  'WhatsApp Intake & AI Validation Engine',
  'Database & Vehicle Grouping Backend',
  'Review & Correction WebApp',
  'Reporting Module, QA & Launch',
]

// Términos del SOW (sin campos de cliente — vienen de ClientInfo)
interface SOWTerms {
  project_description: string
  m1_weeks: string; m1_payment: string
  m2_weeks: string; m2_payment: string
  m3_weeks: string; m3_payment: string
  m4_weeks: string; m4_payment: string
  m5_weeks: string; m5_payment: string
  total_price: string
  initial_payment: string
  final_payment: string
  payment_due_days: string
  late_fee_rate: string
  warranty_days: string
  governing_county: string
}

// Términos del SOW de Soporte & Mantenimiento
interface SupportTerms {
  sow_number: string
  effective_date: string
  project_name: string
  monthly_fee: string
  included_hours: string
  additional_hours_rate: string
  duration_months: string
}

const DEFAULT_SOW_TERMS: SOWTerms = {
  project_description: '',
  m1_weeks: '', m1_payment: '',
  m2_weeks: '', m2_payment: '',
  m3_weeks: '', m3_payment: '',
  m4_weeks: '', m4_payment: '',
  m5_weeks: '', m5_payment: '',
  total_price: '',
  initial_payment: '',
  final_payment: '',
  payment_due_days: '15',
  late_fee_rate: '1.5',
  warranty_days: '30',
  governing_county: 'Miami-Dade',
}

const DEFAULT_SUPPORT_TERMS: SupportTerms = {
  sow_number: '',
  effective_date: '',
  project_name: '',
  monthly_fee: '',
  included_hours: '3',
  additional_hours_rate: '75',
  duration_months: '12',
}

interface AcceptanceTerms {
  project_name: string
  warranty_days: string
  city: string
  governing_county: string
}

const DEFAULT_ACCEPTANCE_TERMS: AcceptanceTerms = {
  project_name: '',
  warranty_days: '30',
  city: '',
  governing_county: 'Orange',
}

export default function SendContract() {
  const navigate = useNavigate()
  const [contractType, setContractType] = useState('nda')
  const [templateId, setTemplateId] = useState('')
  const [defaults, setDefaults] = useState<ContractDefaults | null>(null)
  const [client, setClientState] = useState<ClientInfo>({ ...DEFAULT_CLIENT })
  const [ndaTerms, setNdaTerms] = useState<NDATerms>({ ...DEFAULT_NDA_TERMS })
  const [msaTerms, setMsaTerms] = useState<MSATerms>({ ...DEFAULT_MSA_TERMS })
  const [sowTerms, setSowTerms] = useState<SOWTerms>({ ...DEFAULT_SOW_TERMS })
  const [supportTerms, setSupportTerms] = useState<SupportTerms>({ ...DEFAULT_SUPPORT_TERMS })
  const [acceptanceTerms, setAcceptanceTerms] = useState<AcceptanceTerms>({ ...DEFAULT_ACCEPTANCE_TERMS })
  const [loading, setLoading] = useState(false)
  const [previewLoading, setPreviewLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Carga valores por defecto desde .env vía backend
  useEffect(() => {
    getContractDefaults().then(d => {
      setDefaults(d)
      setNdaTerms(t => ({
        ...t,
        agreement_term:        d.nda.agreement_term,
        non_solicitation_term: d.nda.non_solicitation_term,
        governing_county:      d.nda.governing_county,
      }))
      setMsaTerms(t => ({
        ...t,
        payment_terms:         d.msa.payment_terms,
        late_fee_rate:         d.msa.late_fee_rate,
        agreement_term:        d.msa.agreement_term,
        non_solicitation_term: d.msa.non_solicitation_term,
        governing_county:      d.msa.governing_county,
      }))
      setSowTerms(t => ({
        ...t,
        payment_due_days: d.sow.payment_terms,
        late_fee_rate:    d.sow.late_fee_rate,
        warranty_days:    d.sow.warranty_days,
        governing_county: d.sow.governing_county,
      }))
      setTemplateId(d.nda.template_id)
    }).catch(() => {})
  }, [])

  // Al cambiar tipo de contrato, actualiza template ID (vacío para SOW — usa PDF dinámico)
  useEffect(() => {
    if (!defaults) return
    const id = (contractType === 'sow' || contractType === 'invoice_sow')
      ? ''
      : (defaults[contractType as keyof ContractDefaults]?.template_id ?? '')
    setTemplateId(id)
  }, [contractType, defaults])

  function setClient(key: keyof ClientInfo, value: string) {
    setClientState(c => ({ ...c, [key]: value }))
  }
  function setNda(key: keyof NDATerms, value: string) {
    setNdaTerms(t => ({ ...t, [key]: value }))
  }
  function setMsa(key: keyof MSATerms, value: string) {
    setMsaTerms(t => ({ ...t, [key]: value }))
  }
  function setSow(key: keyof SOWTerms, value: string) {
    setSowTerms(t => ({ ...t, [key]: value }))
  }
  function setSupport(key: keyof SupportTerms, value: string) {
    setSupportTerms(t => ({ ...t, [key]: value }))
  }
  function setAcceptance(key: keyof AcceptanceTerms, value: string) {
    setAcceptanceTerms(t => ({ ...t, [key]: value }))
  }

  // Helpers para los milestones del SOW
  type MilestoneKey = 'm1_weeks'|'m1_payment'|'m2_weeks'|'m2_payment'|'m3_weeks'|'m3_payment'|'m4_weeks'|'m4_payment'|'m5_weeks'|'m5_payment'
  const milestoneWeeksKey  = (i: number) => `m${i+1}_weeks`  as MilestoneKey
  const milestonePayKey    = (i: number) => `m${i+1}_payment` as MilestoneKey

  function buildPayload() {
    const clientFields = {
      client_entity_type: client.client_entity_type,
      client_signer_name: client.client_signer_name,
      client_title:       client.client_title,
      client_address:     client.client_address,
    }

    const nda_fields: NDAFields | undefined =
      contractType === 'nda' ? { ...clientFields, ...ndaTerms } : undefined

    const msa_fields: MSAFields | undefined =
      contractType === 'msa' ? { ...clientFields, ...msaTerms } : undefined

    const sow_fields: SOWFields | undefined =
      (contractType === 'sow' || contractType === 'invoice_sow')
        ? {
            client_signer_name: client.client_signer_name,
            client_title:       client.client_title,
            ...sowTerms,
          }
        : undefined

    const support_sow_fields: SupportSOWFields | undefined =
      contractType === 'support'
        ? {
            client_signer_name: client.client_signer_name,
            client_title:       client.client_title,
            ...supportTerms,
          }
        : undefined

    const acceptance_fields: AcceptanceFields | undefined =
      contractType === 'acceptance'
        ? {
            client_signer_name: client.client_signer_name,
            client_title:       client.client_title,
            ...acceptanceTerms,
          }
        : undefined

    const gen_nda_fields: GenNDAFields | undefined =
      contractType === 'gen_nda'
        ? {
            client_entity_type: client.client_entity_type,
            client_address:     client.client_address,
            client_signer_name: client.client_signer_name,
            client_title:       client.client_title,
            ...ndaTerms,
          }
        : undefined

    const gen_msa_fields: GenMSAFields | undefined =
      contractType === 'gen_msa'
        ? {
            client_entity_type: client.client_entity_type,
            client_address:     client.client_address,
            client_signer_name: client.client_signer_name,
            client_title:       client.client_title,
            ...msaTerms,
          }
        : undefined

    const dynamicTypes = ['sow', 'invoice_sow', 'support', 'acceptance', 'gen_nda', 'gen_msa']

    return {
      client_name:   client.client_name,
      client_email:  client.client_email,
      contract_type: contractType,
      template_id: !dynamicTypes.includes(contractType) && templateId ? templateId : undefined,
      nda_fields,
      msa_fields,
      sow_fields,
      support_sow_fields,
      acceptance_fields,
      gen_nda_fields,
      gen_msa_fields,
    }
  }

  async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      const result = await sendContract(buildPayload())
      navigate(`/contracts/${result.envelope_id}`)
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
    } finally {
      setLoading(false)
    }
  }

  async function handlePreview() {
    setError(null)
    setPreviewLoading(true)
    try {
      const blob = await previewContract(buildPayload())
      const url = URL.createObjectURL(blob)
      window.open(url, '_blank')
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Error desconocido')
    } finally {
      setPreviewLoading(false)
    }
  }

  const isInvoiceSow = contractType === 'invoice_sow'
  const inputClass = 'w-full border border-slate-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500'
  const labelClass = 'block text-sm font-medium text-slate-700 mb-1'
  const sectionLabel = 'text-xs font-semibold text-slate-400 uppercase tracking-wide mb-3'

  return (
    <div className="max-w-xl">
      <h1 className="text-2xl font-semibold text-slate-800 mb-1">Enviar Contrato</h1>
      <p className="text-sm text-slate-500 mb-6">
        Completa los datos del cliente. Tu empresa se agrega automáticamente desde la configuración.
      </p>

      <form onSubmit={handleSubmit} className="space-y-4">

        {/* ── Tipo de contrato ──────────────────────────────────── */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
          <p className={sectionLabel}>Tipo de contrato</p>
          <select
            value={contractType}
            onChange={e => setContractType(e.target.value)}
            className={inputClass}
          >
            {CONTRACT_TYPES.map(t => (
              <option key={t} value={t}>{CONTRACT_TYPE_LABELS[t]}</option>
            ))}
          </select>
        </div>

        {/* ── Datos del cliente ─────────────────────────────────── */}
        <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
          <p className={sectionLabel}>Datos del cliente</p>

          <div className="grid grid-cols-2 gap-3">
            <div className="col-span-2">
              <label className={labelClass}>Nombre de la empresa / cliente</label>
              <input
                required type="text"
                value={client.client_name}
                onChange={e => setClient('client_name', e.target.value)}
                placeholder="Acme Corp LLC"
                className={inputClass}
              />
            </div>

            <div className="col-span-2">
              <label className={labelClass}>Email del cliente</label>
              <input
                required type="email"
                value={client.client_email}
                onChange={e => setClient('client_email', e.target.value)}
                placeholder="john@empresa.com"
                className={inputClass}
              />
            </div>

            <div>
              <label className={labelClass}>Nombre del firmante</label>
              <input
                required type="text"
                value={client.client_signer_name}
                onChange={e => setClient('client_signer_name', e.target.value)}
                placeholder="John Doe"
                className={inputClass}
              />
            </div>

            <div>
              <label className={labelClass}>Título / Cargo</label>
              <input
                required type="text"
                value={client.client_title}
                onChange={e => setClient('client_title', e.target.value)}
                placeholder="CEO, Manager, Owner…"
                className={inputClass}
              />
            </div>

            <div>
              <label className={labelClass}>Tipo de entidad</label>
              <select
                value={client.client_entity_type}
                onChange={e => setClient('client_entity_type', e.target.value)}
                className={inputClass}
              >
                <option value="Individual">Individual</option>
                <option value="LLC">LLC</option>
                <option value="Corporation">Corporation</option>
                <option value="S-Corp">S-Corp</option>
                <option value="Sole Proprietorship">Sole Proprietorship</option>
              </select>
            </div>

            <div className="col-span-2">
              <label className={labelClass}>Dirección del cliente</label>
              <input
                type="text"
                value={client.client_address}
                onChange={e => setClient('client_address', e.target.value)}
                placeholder="456 Client Ave, Miami FL 33101"
                className={inputClass}
              />
            </div>
          </div>
        </div>

        {/* ── Términos NDA ──────────────────────────────────────── */}
        {contractType === 'nda' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <p className={sectionLabel}>Términos del NDA</p>

            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Fecha efectiva del acuerdo</p>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className={labelClass}>Día</label>
                  <input
                    required type="text"
                    value={ndaTerms.effective_day}
                    onChange={e => setNda('effective_day', e.target.value)}
                    placeholder="3"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Mes</label>
                  <select
                    value={ndaTerms.effective_month}
                    onChange={e => setNda('effective_month', e.target.value)}
                    className={inputClass}
                  >
                    {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Año</label>
                  <input
                    required type="text"
                    value={ndaTerms.effective_year}
                    onChange={e => setNda('effective_year', e.target.value)}
                    placeholder="2026"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Duración del acuerdo</label>
                <input
                  type="text"
                  value={ndaTerms.agreement_term}
                  onChange={e => setNda('agreement_term', e.target.value)}
                  placeholder="2 years"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Non-Solicitation (§7)</label>
                <input
                  type="text"
                  value={ndaTerms.non_solicitation_term}
                  onChange={e => setNda('non_solicitation_term', e.target.value)}
                  placeholder="1 year"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Condado (disputas)</label>
                <input
                  type="text"
                  value={ndaTerms.governing_county}
                  onChange={e => setNda('governing_county', e.target.value)}
                  placeholder="Orange"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Términos MSA ──────────────────────────────────────── */}
        {contractType === 'msa' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <p className={sectionLabel}>Términos del MSA</p>

            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Fecha efectiva del acuerdo</p>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className={labelClass}>Día</label>
                  <input
                    required type="text"
                    value={msaTerms.effective_day}
                    onChange={e => setMsa('effective_day', e.target.value)}
                    placeholder="3"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Mes</label>
                  <select
                    value={msaTerms.effective_month}
                    onChange={e => setMsa('effective_month', e.target.value)}
                    className={inputClass}
                  >
                    {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Año</label>
                  <input
                    required type="text"
                    value={msaTerms.effective_year}
                    onChange={e => setMsa('effective_year', e.target.value)}
                    placeholder="2026"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Plazo de pago (días)</label>
                <input
                  type="text"
                  value={msaTerms.payment_terms}
                  onChange={e => setMsa('payment_terms', e.target.value)}
                  placeholder="15"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Interés por mora (% mensual)</label>
                <input
                  type="text"
                  value={msaTerms.late_fee_rate}
                  onChange={e => setMsa('late_fee_rate', e.target.value)}
                  placeholder="1.5"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Vigencia del acuerdo</label>
                <input
                  type="text"
                  value={msaTerms.agreement_term}
                  onChange={e => setMsa('agreement_term', e.target.value)}
                  placeholder="1 year"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Non-Solicitation (§8)</label>
                <input
                  type="text"
                  value={msaTerms.non_solicitation_term}
                  onChange={e => setMsa('non_solicitation_term', e.target.value)}
                  placeholder="1 year"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Condado (disputas)</label>
                <input
                  type="text"
                  value={msaTerms.governing_county}
                  onChange={e => setMsa('governing_county', e.target.value)}
                  placeholder="Miami-Dade"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Términos SOW ──────────────────────────────────────── */}
        {(contractType === 'sow' || contractType === 'invoice_sow') && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-5">
            <p className={sectionLabel}>Términos del SOW</p>

            {/* Proyecto */}
            <div>
              <label className={labelClass}>Descripción del proyecto</label>
              <input
                required type="text"
                value={sowTerms.project_description}
                onChange={e => setSow('project_description', e.target.value)}
                placeholder="Plataforma de tracking vehicular vía WhatsApp"
                className={inputClass}
              />
            </div>

            {/* Milestones table */}
            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Milestones</p>
              <div className="border border-slate-200 rounded-lg overflow-hidden text-sm">
                {/* Header */}
                <div className={`grid ${isInvoiceSow ? 'grid-cols-[1fr_5rem]' : 'grid-cols-[1fr_5rem_6rem]'} bg-slate-700 text-white text-xs font-semibold`}>
                  <div className="px-3 py-2">Milestone</div>
                  <div className="px-3 py-2 text-center">Semanas</div>
                  {!isInvoiceSow && <div className="px-3 py-2 text-center">Pago (USD)</div>}
                </div>
                {/* Rows */}
                {(isInvoiceSow ? INVOICE_SOW_MILESTONE_NAMES : SOW_MILESTONE_NAMES).map((name, i) => (
                  <div
                    key={i}
                    className={`grid ${isInvoiceSow ? 'grid-cols-[1fr_5rem]' : 'grid-cols-[1fr_5rem_6rem]'} border-t border-slate-200 ${i % 2 === 1 ? 'bg-slate-50' : 'bg-white'}`}
                  >
                    <div className="px-3 py-2 text-slate-700 flex items-center">
                      <span className="text-slate-400 mr-2 font-medium">{i + 1}.</span>
                      {name}
                    </div>
                    <div className="px-2 py-1.5 flex items-center">
                      <input
                        type="text"
                        value={sowTerms[milestoneWeeksKey(i)]}
                        onChange={e => setSow(milestoneWeeksKey(i), e.target.value)}
                        placeholder="2"
                        className="w-full border border-slate-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                    {!isInvoiceSow && (
                      <div className="px-2 py-1.5 flex items-center">
                        <input
                          type="text"
                          value={sowTerms[milestonePayKey(i)]}
                          onChange={e => setSow(milestonePayKey(i), e.target.value)}
                          placeholder="2500"
                          className="w-full border border-slate-300 rounded px-2 py-1 text-sm text-center focus:outline-none focus:ring-1 focus:ring-blue-500"
                        />
                      </div>
                    )}
                  </div>
                ))}
                {/* Total — solo para SOW por milestone */}
                {!isInvoiceSow && (
                  <div className="grid grid-cols-[1fr_5rem_6rem] border-t-2 border-slate-300 bg-slate-100">
                    <div className="px-3 py-2 text-slate-700 font-semibold col-span-2 flex items-center justify-end pr-4">
                      TOTAL (USD)
                    </div>
                    <div className="px-2 py-1.5 flex items-center">
                      <input
                        required type="text"
                        value={sowTerms.total_price}
                        onChange={e => setSow('total_price', e.target.value)}
                        placeholder="15000"
                        className="w-full border border-slate-300 rounded px-2 py-1 text-sm text-center font-semibold focus:outline-none focus:ring-1 focus:ring-blue-500"
                      />
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Pago en dos cuotas — solo para Invoice Automation SOW */}
            {isInvoiceSow && (
              <div className="grid grid-cols-3 gap-3">
                <div>
                  <label className={labelClass}>Pago inicial (USD)</label>
                  <input
                    required type="text"
                    value={sowTerms.initial_payment}
                    onChange={e => setSow('initial_payment', e.target.value)}
                    placeholder="2000"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Pago final (USD)</label>
                  <input
                    required type="text"
                    value={sowTerms.final_payment}
                    onChange={e => setSow('final_payment', e.target.value)}
                    placeholder="2500"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>TOTAL (USD)</label>
                  <input
                    required type="text"
                    value={sowTerms.total_price}
                    onChange={e => setSow('total_price', e.target.value)}
                    placeholder="4500"
                    className={`${inputClass} font-semibold`}
                  />
                </div>
              </div>
            )}

            {/* Términos de pago y garantía */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Plazo de pago (días)</label>
                <input
                  type="text"
                  value={sowTerms.payment_due_days}
                  onChange={e => setSow('payment_due_days', e.target.value)}
                  placeholder="15"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Interés por mora (% mensual)</label>
                <input
                  type="text"
                  value={sowTerms.late_fee_rate}
                  onChange={e => setSow('late_fee_rate', e.target.value)}
                  placeholder="1.5"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Garantía post-lanzamiento (días)</label>
                <input
                  type="text"
                  value={sowTerms.warranty_days}
                  onChange={e => setSow('warranty_days', e.target.value)}
                  placeholder="30"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Condado (disputas)</label>
                <input
                  type="text"
                  value={sowTerms.governing_county}
                  onChange={e => setSow('governing_county', e.target.value)}
                  placeholder="Orange"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Términos Support SOW ─────────────────────────────── */}
        {contractType === 'support' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <p className={sectionLabel}>Soporte &amp; Mantenimiento — Standard Plan</p>

            {/* SOW metadata */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>SOW No.</label>
                <input
                  type="text"
                  value={supportTerms.sow_number}
                  onChange={e => setSupport('sow_number', e.target.value)}
                  placeholder="SOW-2026-001"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Fecha efectiva</label>
                <input
                  type="text"
                  value={supportTerms.effective_date}
                  onChange={e => setSupport('effective_date', e.target.value)}
                  placeholder="June 15, 2026"
                  className={inputClass}
                />
              </div>
              <div className="col-span-2">
                <label className={labelClass}>Nombre del proyecto / plataforma</label>
                <input
                  type="text"
                  value={supportTerms.project_name}
                  onChange={e => setSupport('project_name', e.target.value)}
                  placeholder="Automated Invoice Processing with AI"
                  className={inputClass}
                />
              </div>
            </div>

            {/* Commercial terms */}
            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Fee mensual (USD)</label>
                <input
                  required type="text"
                  value={supportTerms.monthly_fee}
                  onChange={e => setSupport('monthly_fee', e.target.value)}
                  placeholder="250"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Horas incluidas / mes</label>
                <input
                  type="text"
                  value={supportTerms.included_hours}
                  onChange={e => setSupport('included_hours', e.target.value)}
                  placeholder="3"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Tarifa horas adicionales (USD/hr)</label>
                <input
                  type="text"
                  value={supportTerms.additional_hours_rate}
                  onChange={e => setSupport('additional_hours_rate', e.target.value)}
                  placeholder="75"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Duración inicial (meses)</label>
                <input
                  type="text"
                  value={supportTerms.duration_months}
                  onChange={e => setSupport('duration_months', e.target.value)}
                  placeholder="12"
                  className={inputClass}
                />
              </div>
            </div>

            {/* Fixed SLA preview */}
            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">SLA — Standard Plan (fijo)</p>
              <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
                {[
                  { label: 'Critical', desc: 'Platform down or invoices not processing', time: '24–48 hours', bg: 'bg-red-50' },
                  { label: 'High',     desc: 'Data extraction errors / notification failures', time: '48 hours',    bg: 'bg-orange-50' },
                  { label: 'Medium',   desc: 'Minor adjustments / technical inquiries',         time: '72 hours',    bg: 'bg-yellow-50' },
                  { label: 'Low',      desc: 'Requested improvements or changes',               time: 'N/A',         bg: 'bg-green-50' },
                ].map(row => (
                  <div key={row.label} className={`grid grid-cols-[4rem_1fr_6rem] border-t border-slate-100 first:border-t-0 px-3 py-2 ${row.bg}`}>
                    <span className="font-semibold text-slate-700">{row.label}</span>
                    <span className="text-slate-500">{row.desc}</span>
                    <span className="text-right font-medium text-slate-700">{row.time}</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Acceptance Certificate ────────────────────────────── */}
        {contractType === 'acceptance' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <p className={sectionLabel}>Certificado de Aceptación Final</p>

            <div>
              <label className={labelClass}>Nombre del proyecto</label>
              <input
                required type="text"
                value={acceptanceTerms.project_name}
                onChange={e => setAcceptance('project_name', e.target.value)}
                placeholder="Vehicle Tracking & Booking Platform"
                className={inputClass}
              />
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Garantía post-lanzamiento (días)</label>
                <input
                  type="text"
                  value={acceptanceTerms.warranty_days}
                  onChange={e => setAcceptance('warranty_days', e.target.value)}
                  placeholder="30"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Ciudad (firma)</label>
                <input
                  type="text"
                  value={acceptanceTerms.city}
                  onChange={e => setAcceptance('city', e.target.value)}
                  placeholder="Orlando"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Condado (disputas)</label>
                <input
                  type="text"
                  value={acceptanceTerms.governing_county}
                  onChange={e => setAcceptance('governing_county', e.target.value)}
                  placeholder="Orange"
                  className={inputClass}
                />
              </div>
            </div>

            {/* Fixed deliverables preview */}
            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Entregables incluidos (fijos)</p>
              <div className="border border-slate-200 rounded-lg overflow-hidden text-xs">
                {[
                  'Corporate Website & Booking System',
                  'WhatsApp API Integration',
                  'Tracking Automation Backend',
                  'Management WebApp Panel',
                ].map((d, i) => (
                  <div key={i} className={`flex items-center gap-2 px-3 py-2 border-t border-slate-100 first:border-t-0 ${i % 2 === 1 ? 'bg-slate-50' : ''}`}>
                    <span className="w-4 h-4 rounded-full bg-green-100 text-green-700 flex items-center justify-center font-bold text-[10px] shrink-0">{i + 1}</span>
                    <span className="text-slate-600">{d}</span>
                    <span className="ml-auto font-semibold text-green-700">ACCEPTED</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ── Términos NDA (Generated PDF) ─────────────────────── */}
        {contractType === 'gen_nda' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <p className={sectionLabel}>Términos del NDA</p>

            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Fecha efectiva del acuerdo</p>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className={labelClass}>Día</label>
                  <input
                    required type="text"
                    value={ndaTerms.effective_day}
                    onChange={e => setNda('effective_day', e.target.value)}
                    placeholder="3"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Mes</label>
                  <select
                    value={ndaTerms.effective_month}
                    onChange={e => setNda('effective_month', e.target.value)}
                    className={inputClass}
                  >
                    {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Año</label>
                  <input
                    required type="text"
                    value={ndaTerms.effective_year}
                    onChange={e => setNda('effective_year', e.target.value)}
                    placeholder="2026"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Duración del acuerdo (§11)</label>
                <input
                  type="text"
                  value={ndaTerms.agreement_term}
                  onChange={e => setNda('agreement_term', e.target.value)}
                  placeholder="2 years"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Non-Solicitation (§8)</label>
                <input
                  type="text"
                  value={ndaTerms.non_solicitation_term}
                  onChange={e => setNda('non_solicitation_term', e.target.value)}
                  placeholder="1 year"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Condado (disputas §12)</label>
                <input
                  type="text"
                  value={ndaTerms.governing_county}
                  onChange={e => setNda('governing_county', e.target.value)}
                  placeholder="Miami-Dade"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Términos MSA (Generated PDF) ─────────────────────── */}
        {contractType === 'gen_msa' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 space-y-4">
            <p className={sectionLabel}>Términos del MSA</p>

            <div>
              <p className="text-xs font-medium text-slate-500 mb-2">Fecha efectiva del acuerdo</p>
              <div className="grid grid-cols-3 gap-2">
                <div>
                  <label className={labelClass}>Día</label>
                  <input
                    required type="text"
                    value={msaTerms.effective_day}
                    onChange={e => setMsa('effective_day', e.target.value)}
                    placeholder="3"
                    className={inputClass}
                  />
                </div>
                <div>
                  <label className={labelClass}>Mes</label>
                  <select
                    value={msaTerms.effective_month}
                    onChange={e => setMsa('effective_month', e.target.value)}
                    className={inputClass}
                  >
                    {MONTHS.map(m => <option key={m} value={m}>{m}</option>)}
                  </select>
                </div>
                <div>
                  <label className={labelClass}>Año</label>
                  <input
                    required type="text"
                    value={msaTerms.effective_year}
                    onChange={e => setMsa('effective_year', e.target.value)}
                    placeholder="2026"
                    className={inputClass}
                  />
                </div>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className={labelClass}>Vigencia del acuerdo (§14)</label>
                <input
                  type="text"
                  value={msaTerms.agreement_term}
                  onChange={e => setMsa('agreement_term', e.target.value)}
                  placeholder="1 year"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Non-Solicitation (§8)</label>
                <input
                  type="text"
                  value={msaTerms.non_solicitation_term}
                  onChange={e => setMsa('non_solicitation_term', e.target.value)}
                  placeholder="1 year"
                  className={inputClass}
                />
              </div>
              <div>
                <label className={labelClass}>Condado (disputas §16)</label>
                <input
                  type="text"
                  value={msaTerms.governing_county}
                  onChange={e => setMsa('governing_county', e.target.value)}
                  placeholder="Miami-Dade"
                  className={inputClass}
                />
              </div>
            </div>
          </div>
        )}

        {/* ── Template ID override (solo NDA / MSA) ─────────────── */}
        {contractType !== 'sow' && contractType !== 'invoice_sow' && contractType !== 'support' && contractType !== 'acceptance' && contractType !== 'gen_nda' && contractType !== 'gen_msa' && (
          <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-6">
            <label className={labelClass}>
              Template ID <span className="text-slate-400 font-normal">(opcional)</span>
            </label>
            <input
              type="text"
              value={templateId}
              onChange={e => setTemplateId(e.target.value)}
              placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
              className={`${inputClass} font-mono`}
            />
          </div>
        )}

        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 rounded-lg px-4 py-3 text-sm">
            {error}
          </div>
        )}

        <div className="flex gap-3">
          {isInvoiceSow && (
            <button
              type="button"
              onClick={handlePreview}
              disabled={previewLoading || loading}
              className="flex-1 bg-white hover:bg-slate-50 disabled:opacity-60 text-slate-700 font-medium py-2.5 rounded-lg text-sm border border-slate-300 transition-colors"
            >
              {previewLoading ? 'Generando…' : 'Vista Previa'}
            </button>
          )}
          <button
            type="submit"
            disabled={loading || previewLoading}
            className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:opacity-60 text-white font-medium py-2.5 rounded-lg text-sm transition-colors"
          >
            {loading ? 'Enviando…' : 'Enviar Contrato'}
          </button>
        </div>
      </form>
    </div>
  )
}
