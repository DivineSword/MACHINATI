export type RequestRow = {
  id: number;
  farmer_phone: string;
  status: string;
  created_at: string;
  priority_score: number;
  priority_reason: string;
  machine_fit: 'match' | 'transport_review' | 'date_review' | 'unavailable' | 'not_specified';
  machine_fit_reason: string;
  matching_machines: Array<{ id: number; name: string; location: string | null; compatibility_notes: string | null }>;
  payload: {
    machine_type?: string;
    operation?: string;
    area_hectares?: number;
    location?: string;
    preferred_date?: string;
    preferred_date_text?: string;
    urgency_level?: 'normal' | 'urgent' | 'critical' | null;
    urgency_reason?: string | null;
    urgent_window_start?: string | null;
    urgent_window_end?: string | null;
    verified_by?: string | null;
  };
};

export type MachineRow = {
  id: number;
  name: string;
  machine_type: string;
  location: string | null;
  hourly_rate: number | null;
  available: number | boolean;
  owner_type: 'company' | 'partner';
  reserved_for_own_use: number | boolean;
  available_from: string | null;
  available_to: string | null;
  compatibility_notes: string | null;
};