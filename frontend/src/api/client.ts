const BASE = '/contracts'

export interface Envelope {
  envelope_id: string
  status: string
  email_subject: string | null
  sent_date: string | null
  completed_date: string | null
  decline_reason?: string | null
}

export interface NDAFields {
  // Cliente (Receiving Party) — cuerpo del documento
  client_entity_type: string
  client_address: string
  // Firmante del cliente
  client_signer_name: string
  client_title: string
  // Fecha separada en tres campos
  effective_day: string
  effective_month: string
  effective_year: string
  // Otros
  agreement_term: string
  non_solicitation_term: string
  governing_county: string
}

export interface MSAFields {
  // Cliente — cuerpo del documento
  client_entity_type: string
  client_address: string
  // Firmante del cliente
  client_signer_name: string
  client_title: string
  effective_day: string
  effective_month: string
  effective_year: string
  payment_terms: string
  late_fee_rate: string
  agreement_term: string
  non_solicitation_term: string
  governing_county: string
}

export interface SOWFields {
  client_signer_name: string
  client_title: string
  project_description: string
  m1_weeks: string; m1_payment: string
  m2_weeks: string; m2_payment: string
  m3_weeks: string; m3_payment: string
  m4_weeks: string; m4_payment: string
  m5_weeks: string; m5_payment: string
  total_price: string
  payment_due_days: string
  late_fee_rate: string
  warranty_days: string
  governing_county: string
}

export interface SupportSOWFields {
  client_signer_name: string
  client_title: string
  monthly_fee: string
  included_hours: string
  duration_months: string
  sla_critical_hours: string
  sla_medium_hours: string
  sla_low_hours: string
  governing_county: string
}

export interface AcceptanceFields {
  client_signer_name: string
  client_title: string
  project_name: string
  warranty_days: string
  city: string
  governing_county: string
}

export interface GenNDAFields {
  client_entity_type: string
  client_address: string
  client_signer_name: string
  client_title: string
  effective_day: string
  effective_month: string
  effective_year: string
  agreement_term: string
  non_solicitation_term: string
  governing_county: string
}

export interface SendContractPayload {
  client_name: string
  client_email: string
  contract_type: string
  template_id?: string
  nda_fields?: NDAFields
  msa_fields?: MSAFields
  sow_fields?: SOWFields
  support_sow_fields?: SupportSOWFields
  acceptance_fields?: AcceptanceFields
  gen_nda_fields?: GenNDAFields
  embedded?: boolean
}

export interface SendContractResponse {
  envelope_id: string
  status: string
  signing_url?: string | null
}

export async function listContracts(fromDate?: string): Promise<Envelope[]> {
  const url = fromDate ? `${BASE}?from_date=${fromDate}` : BASE
  const res = await fetch(url)
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return res.json()
}

export async function getContractStatus(envelopeId: string): Promise<Envelope> {
  const res = await fetch(`${BASE}/${envelopeId}/status`)
  if (!res.ok) throw new Error(`Error ${res.status}`)
  return res.json()
}

export async function sendContract(payload: SendContractPayload): Promise<SendContractResponse> {
  const res = await fetch(`${BASE}/send`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({}))
    throw new Error(err.detail || `Error ${res.status}`)
  }
  return res.json()
}

export function downloadContract(envelopeId: string) {
  window.open(`${BASE}/${envelopeId}/download`, '_blank')
}

export interface ContractDefaults {
  nda: { template_id: string; agreement_term: string; non_solicitation_term: string; governing_county: string }
  msa: { template_id: string; payment_terms: string; late_fee_rate: string; agreement_term: string; non_solicitation_term: string; governing_county: string }
  sow: { template_id: string; warranty_days: string; payment_terms: string; late_fee_rate: string; governing_county: string }
}
// note: sow.template_id is empty string — SOW uses dynamic PDF generation, not a DocuSign template

export async function getContractDefaults(): Promise<ContractDefaults> {
  const res = await fetch('/config/defaults')
  if (!res.ok) throw new Error('No se pudieron cargar los valores por defecto')
  return res.json()
}
