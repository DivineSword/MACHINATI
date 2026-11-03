export type RequestRow = {
  id: number;
  farmer_phone: string;
  status: string;
  created_at: string;
  payload: {
    machine_type?: string;
    operation?: string;
    area_hectares?: number;
    location?: string;
    preferred_date?: string;
    preferred_date_text?: string;
  };
};

export type MachineRow = {
  id: number;
  name: string;
  machine_type: string;
  location: string | null;
  hourly_rate: number | null;
  available: number | boolean;
};